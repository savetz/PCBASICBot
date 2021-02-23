# PCBASICBot
 The code that runs the PC BASIC bot at https://twitter.com/PCBASICBot

I'm sharing this so people can use this as a stepping stone to making their own, different bots.

Documentation for using the bot is at https://pcbasicbot.com

The main twitter posting code is based on what I learned from "The Reply to Mentions Bot" at https://realpython.com/twitter-bot-python-tweepy/#the-config-module

Dependencies:
- A Twitter account, and API keys for it https://developer.twitter.com/en/products/twitter-api
- Tweepy. Specifically the fork that allows video uploads. https://github.com/tweepy/tweepy/pull/1414 They plan on folding that feature into the main program but as of this writing, haven't.
- DOSBox: https://www.dosbox.com
- PC BASIC emulator: https://robhagemans.github.io/pcbasic/
- ffmpeg, for processing video files: https://ffmpeg.org
- and in the assets/ directory: QBASIC 1.1, named QBASIC.EXE. This is not provided in this repository due to copyright.
- An X Virtual Frame Buffer running on display 97 (/usr/bin/Xvfb :97 -ac -screen 0 1024x768x24)
