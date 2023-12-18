# bot.py
import os
import random
from simpletransformers.language_generation import LanguageGenerationModel
import discord

TOKEN = 'MTA0MDEyMzcwMTc4MzQyOTEyMQ.GZqkg8.ioMu3DBM1e8vKb4vm7Az91sA-Y2RG6XLDpH-yk' 
PATH_TO_MODEL = "models/best_model/" 
DEDICATED_CHANNEL_NAME = 'general' 

USE_CUDA = False


EXPERIMENTAL_MEMORY = True
EXPERIMENTAL_MEMORY_LENGTH = 700 
intent = discord.Intents.all()
client = discord.Client(intents=intent)
@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')


memory = ''

def genCleanMessage(optPrompt):
        global memory
        formattedPrompt = '<|sor|>' + optPrompt + '<|eor|><|sor|>'
        if (len(memory) == 0):
            formattedPrompt = '<|soss|><|sot|>' + optPrompt + '<|eot|><|sor|>'
        memory += formattedPrompt
        print('\nPROMPT:' + formattedPrompt + '\n')
        print('\nMEMORY:' + memory + '\n')
        model = LanguageGenerationModel("gpt2", PATH_TO_MODEL, use_cuda=USE_CUDA)
        text_generation_parameters = {
			'max_length': 100,
            'repetition_penalty': 1.01,
			'num_return_sequences': 1,
			'prompt': memory,
			'temperature': 0.9, #0.8
			'top_k': 40,
	}
        output_list = model.generate(prompt=memory, args=text_generation_parameters)
        response = output_list[0]
        response = response.replace(memory, '')
        i = 0
        cleanStr = ''
        print(response)
        for element in response:
            if element == '<':
                i = 1
            if i == 0 and element != '!':
                cleanStr += element
            if element == '>':
                i = 0
        if not cleanStr:
            cleanStr = 'Idk how to respond to that lol. I broke.'
        memory += cleanStr + "<|eor|>"
        return cleanStr

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == '!reset' and str(message.channel) == DEDICATED_CHANNEL_NAME:
        global memory
        memory = ''
        await message.channel.send('```convo reset```')
        print(memory)
        return
    if str(message.channel) == DEDICATED_CHANNEL_NAME:
        if (len(memory) > EXPERIMENTAL_MEMORY_LENGTH) or (not EXPERIMENTAL_MEMORY):
            memory = ''
        prompt = message.content
        
        print('messages '+ message.content)
        genMessage = genCleanMessage(prompt)
        await message.channel.send(genMessage)
    elif message.content == 'raise-exception':
        raise discord.DiscordException

client.run(TOKEN)