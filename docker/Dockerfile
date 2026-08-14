# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files into container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir discord.py aiohttp python-dotenv

# Run the bot
CMD ["python", "bot.py"]
