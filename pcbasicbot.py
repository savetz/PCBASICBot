#PCBASICBot by @KaySavetz. 2020-2021.

import tweepy
import logging
from botConfig import create_api
import time
from shutil import copyfile
import os,sys,shutil
import subprocess
from datetime import datetime
from unidecode import unidecode
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id, tweet_mode='extended').items():
        new_since_id = max(tweet.id, new_since_id)

        logger.info(f"Tweet from {tweet.user.name}")

        #remove @ mentions, leaving just the BASIC code
        basiccode = re.sub('^(@.+?\s)+','',tweet.full_text)

        basiccode = unidecode(basiccode)

        #unescape >, <, and &
        basiccode = basiccode.replace("&lt;", "<")
        basiccode = basiccode.replace("&gt;", ">")
        basiccode = basiccode.replace("&amp;", "&")

        #look for start time command
        exp = "{\w*?B(\d\d?)\w*(?:}|\s)" # {B\d\d  B= Begin
        result = re.search(exp,basiccode)
        if result:  
            starttime = int(result.group(1))
            logger.info(f" Requests start at {starttime} seconds")
        else:
            starttime = 3

        #look for length of time to record command
        exp = "{\w*?S(\d\d?)\w*(?:}|\s)" # {S\d\d  S= Seconds to record
        result=re.search(exp,basiccode)
        if result:
            recordtime = int(result.group(1))
            logger.info(f" Requests record for {recordtime} seconds")
        else:
            recordtime = 5
        if recordtime <1:
            recordtime=1

        basicMode=1 #default is GW-BASIC
        green=0    #default is color

        exp = "{\w*?G\w*(?:}|\s)" #{G
        if re.search(exp,basiccode):
            green=1 #greenscreen
            logger.info("requests green screen")
        
        exp = "{\w*?A\w*(?:}|\s)" #{A
        if re.search(exp,basiccode):
            green=2 #amberscreen
            logger.info("requests amber screen")

        exp = "{\w*?Q\w*(?:}|\s)" #{Q
        if re.search(exp,basiccode):
            basicMode=0
            logger.info("requests QBASIC")

        #remove any { command
        exp = "{\w*(?:}|\s)" #{anything till space or }
        basiccode = re.sub(exp,'',basiccode)

        #remove use of SHELL for security
        shellFix = re.compile(re.escape('shell'), re.IGNORECASE)
        basiccode = shellFix.sub('REM ',basiccode)
        
        #whitespace
        basiccode = basiccode.strip()

        #halt if string is empty
        if not basiccode:
            logger.info("!!! basiccode string is empty, SKIPPING")
            continue;

        #halt if string doesn't start with a line number AND it's GW-BASIC
        if basicMode==1 and not re.match("^[0-9]", basiccode):
            logger.info("!!! basiccode doesn't start with a line number, SKIPPING")
            continue;

        logger.info("Fresh c: directory")
        if os.path.exists("working"):
            os.chmod('working/', 0o755) #make it writable so we can wipe it
            shutil.rmtree('working') #wipe it
        os.mkdir('working')
        copyfile('assets/QBASIC.EXE','working/QBASIC.EXE')

        outputFile = open('working/BOT.BAS','w')
        outputFile.write(basiccode)
        outputFile.close()

        os.chmod('working/', 0o555) #read-only to prevent BASIC code from writing to linux

        logger.info("Firing up emulator")

        if basicMode==0: #QBASIC
           if green==0:
               cmd = 'dosbox -conf assets/color.conf'.split()
           else:
               cmd = 'dosbox -conf assets/hercules.conf'.split() 
           ## "dosbox -userconf -conf whatever.conf" doesn't work as advertised so separate files
           emuPid = subprocess.Popen(cmd)
           logger.info(f"   Process ID {emuPid.pid}")
           time.sleep(2) #give DOSbox a sec to start up before we start typing

            ## WHY I'M DOING IT THIS WAY
            ## 1) need to press F11 once for amber mode, twice for green. DOSbox doesn't let you
            ##    do it via config file
            ## 2) but pressing F11 triggers QBASIC's "press any key to continue" after the program
            ##    ends, dumping you into the editor. So F11 must be pressed before running QBASIC.
            ##    that's why we're using xdotool to involve QBASIC instead of the DOSbox config file
            ## 3) xdotool type command doesn't work reliably in combination with key command.
           if green==0:
               os.system('xdotool search --class "DOSBox" key Q B A S I C space slash R U N space B O T period B A S Return')
           if green==1:
               os.system('xdotool search --class "DOSBox" key F11 F11 Q B A S I C space slash R U N space B O T period B A S Return')
               #this should work but doesn't:
               #os.system('xdotool search --class "DOSBox" key F11 F11')
               #os.system('xdotool type \'QBASIC /RUN BOT.BAS\r\'')
           if green==2:
               os.system('xdotool search --class "DOSBox" key F11 Q B A S I C space slash R U N space B O T period B A S Return')

        else: #GWBASIC
            if green==0:
                colorName='rgb'
            elif green==1:
                colorName='green'
            elif green==2:
                colorName='amber'
            cmd = ('/home/atari8/.local/bin/pcbasic working/BOT.BAS --lpt1=FILE:/dev/null -f=0 --serial-buffer-size=0 --monitor=' + colorName).split() 
            emuPid = subprocess.Popen(cmd)
            logger.info(f"   Process ID {emuPid.pid}")

        time.sleep(starttime) 

        logger.info("Recording with ffmpeg")
        if basicMode==0:
            result = os.system(f'/usr/bin/ffmpeg -y -hide_banner -loglevel warning -draw_mouse 0 -f x11grab -r 30 -video_size 640x400 -i :97+0,0 -q:v 0 -pix_fmt yuv422p -t {recordtime} working-video/BIG.mp4')
        else: #basicMode=1 #PCBASIC/GWBASIC
            result = os.system(f'/usr/bin/ffmpeg -y -hide_banner -loglevel warning -draw_mouse 0 -f x11grab -r 30 -video_size 830x630 -i :97+90,60 -q:v 0 -pix_fmt yuv422p -t {recordtime} working-video/BIG.mp4')

        logger.info("Stopping emulator")
        emuPid.kill()

        logger.info("Converting video")
        result = os.system('ffmpeg -loglevel warning -y -i working-video/BIG.mp4 -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -pix_fmt yuv420p -strict experimental -r 30 -t 2:20 -acodec aac -vb 1024k -minrate 1024k -maxrate 1024k -bufsize 1024k -ar 44100 -ac 2 working-video/SMALL.mp4')
        #per https://gist.github.com/nikhan/26ddd9c4e99bbf209dd7#gistcomment-3232972

        logger.info("Uploading video")  

        media = api.media_upload("working-video/SMALL.mp4")

        logger.info(f"Media ID is {media.media_id}")

        time.sleep(5)
#TODO replace with get_media_upload_status per https://github.com/tweepy/tweepy/pull/1414

        logger.info(f"Posting tweet to @{tweet.user.screen_name}")
        tweettext = f"@{tweet.user.screen_name} "
        post_result = api.update_status(auto_populate_reply_metadata=False, status=tweettext, media_ids=[media.media_id], in_reply_to_status_id=tweet.id)

        logger.info("Done!")

    return new_since_id

def main():
    os.chdir('/home/atari8/pcbasicbot/')

    api = create_api()

    now = datetime.now()
    logger.info("START TIME:")
    logger.info(now.strftime("%Y %m %d %H:%M:%S")) 

    try:
        sinceFile = open('sinceFile.txt','r')
        since_id = sinceFile.read()
    except:
        sinceFile = open('sinceFile.txt','w')
        sinceFile.write("1")
        logger.info("created new sinceFile")
        since_id = 1

    sinceFile.close()       
    since_id = int(since_id)
    logger.info(f"Starting since_id {since_id}")
    
    os.environ["DISPLAY"] = ":97"

    while True:
        didatweet=0
        new_since_id = check_mentions(api, since_id)

        if new_since_id != since_id:
            since_id = new_since_id
            logger.info(f"Since_id now {since_id}")
        
            sinceFile = open('sinceFile.txt','w')
            sinceFile.write(str(since_id))
            sinceFile.close()
            didatweet=1

        if didatweet==0:
            logger.info("Waiting...")
            time.sleep(120)

if __name__ == "__main__":
    main()
    
