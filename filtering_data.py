#!/usr/bin/env python3
import random

from datetime import datetime

from configparser import ConfigParser

from db import (Comment as db_Comment, Submission as db_Submission)

import concurrent.futures


author_blacklist = ['automoderator', 'nfl_mod', 'totesmessenger', 'haikubot-1911', 'gfy_mirror', 'should_have_listened',
	'nice-scores', 'repliesnice', 'redditstreamable', 'twittertostreamable', 'streamablemirrors', 'originalpostsearcher',
	'b0trank', 'vredditdownloader', 'tweetposter', 'link-reply-bot', 'clickablelinkbot', 'i-am-dad-bot', 'GitHubPermalinkBot',
	'Freedom_Unit_Bot', 'LearnProgramming_Bot', 'CodeFormatHelperBot']

negative_keywords = ['NSFW', 'fuck', 'shit']

training_subreddits = ['askscience','AskScienceDiscussion','singularity', 'futurology']

text_removed = ['[removed]', '[deleted]']


def gather_comments_for_submission(sub):

	if any(s in sub.selftext for s in negative_keywords):
		print(f"{sub.id} contains negative keywords")
		return

	if any(s in sub.selftext for s in text_removed):
		print(f"blacklist selftext: {sub.selftext}")
		return

	if sub.author.lower() in author_blacklist:
		print(f"author blacklist {sub.author}")
		return

	top_rated_comments = list(db_Comment.select().where((db_Comment.link_id == f't3_{sub.id}') &
		(fn.Lower(db_Comment.author.not_in(author_blacklist))) & (~db_Comment.is_url_only)))

	for tr_comment in top_rated_comments:

		print(f"starting top rated comments loop {sub.id}")


		if tr_comment.submission().is_self:

			text_gen_string = "<|eoss|>"
		else:

			text_gen_string = "<|eols|>"

		ancestor = tr_comment
		comments_counted = 0
		while ancestor is not None:

			if (ancestor.author.lower() in author_blacklist or
				ancestor.author.lower().endswith('bot')):

				break

			if isinstance(ancestor, db_Comment):
				if any(s in ancestor.body for s in text_removed):
					print("blacklist text... breaking")
					break

				record_string = f"<|sor|>{ancestor.body}<|eor|>"


				text_gen_string = record_string + text_gen_string
				comments_counted += 1

			elif isinstance(ancestor, db_Submission):

				if ancestor.is_self:

					record_string = f"<|soss|><|sot|>{ancestor.title}<|eot|><|sost|>{ancestor.selftext}<|eost|>"
				else:

					record_string = f"<|sols|><|sot|>{ancestor.title}<|eot|><|sol|><|eol|>"

				text_gen_string = record_string + text_gen_string
				break
			ancestor = ancestor.parent()

		if text_gen_string.startswith("<|sols") or text_gen_string.startswith('<|soss') and comments_counted > 0:

			return text_gen_string


def main():

	random.seed()

	bot_name = "training_output"

	all_submissions = []
	# all submissions ordered by date
	all_submissions = list(db_Submission.select().
		where((fn.Lower(db_Submission.subreddit).in_([s.lower() for s in training_subreddits])) &
				(fn.Lower(db_Submission.author).not_in([a.lower() for a in author_blacklist]))))

	random.shuffle(all_submissions)

	split_point = int(len(all_submissions) * 0.9)
	training_submissions = all_submissions[:split_point]
	eval_submissions = all_submissions[split_point:]

	print(f'{len(training_submissions)} training submissions, {len(eval_submissions)} evaluation submissions')


	date_string = datetime.today().strftime('%d%m%y_%H%M')
	counter = 0

	with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
		filename = f'{bot_name}_{date_string}_training.txt'

		with open(filename, 'a', encoding='utf-8') as fd:
			for sub, output_text_gen_string in zip(training_submissions, executor.map(gather_comments_for_submission, training_submissions)):
				counter += 1
				if output_text_gen_string:
					fd.write(f'{output_text_gen_string}' + '<|endoftext|>\n')
				print(f'subs counted: {counter}. {round(counter/len(all_submissions), 2)}')

		filename = f'{bot_name}_{date_string}_eval.txt'
		with open(filename, 'a', encoding='utf-8') as fd:
			for sub, output_text_gen_string in zip(eval_submissions, executor.map(gather_comments_for_submission, eval_submissions)):
				counter += 1
				if output_text_gen_string:
					fd.write(f'{output_text_gen_string}' + '<|endoftext|>\n')
				print(f'subs counted: {counter}. {round(counter/len(all_submissions), 2)}')


if __name__ == '__main__':
	main()
