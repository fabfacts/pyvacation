#!/usr/bin/env python
#
#
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import sys
import re
try:
   import sqlite3
   sqlite = sqlite3
except:
   import sqlite
import getopt
import logging
import smtplib
import string
import syslog
import inspect

#########################################################################################################################
#  Global variables

dbname = "/var/spool/postfix/vacation/localUsers.db"
domainame = "your-mailserver-domainname"
virtualpath = "/etc/postfix/autoreply_virtual"
logfile = "/var/spool/postfix/vacation/error.log"
postmap = "/usr/sbin/postmap"
defaultmsgPath = "/etc/postfix/autoresponder/defaultReply.txt"

# mailing lists tags
listsTag = ( 'List-ID:' , 'List-Id:' , 'Mailing-List:' , 'X-Mailing-List:' )

#########################################################################################################################
#  Logging 

FORMAT = "%(asctime)-15s %(user)-8s %(message)s"
logging.basicConfig(format=FORMAT,
                    filename=logfile,
                    filemode='append')
logging.basicConfig()

# set the username 
#d = {'user': os.getlogin() }

#########################################################################################################################
# return the current function name

def whoami():
    return inspect.stack()[1][3]

#########################################################################################################################
# help menus

def usage():
    print "Usage: %s [Options] " % sys.argv[0]
    print
    print "Options:"
    print
    print "        -a, --add :          Add a new user into the users database"
    print "        -r, --remove :       Remove ia user from the database"
    print "        -e, --enable :       enable the autoresponder"
    print "        -d, --disable :      disable the autoresponder"
    print "        -D, --deliver :      deliver an email"
    print "        -f, --file :         load reply message from a file"
    print "        -u, --update :       update user data"
    print "        -A, --autoreply :    execute commands trough email"
    print
    print " -u, --use [option]         Shows a specific option usage"
    print "                            e.g: --use add"
    print 
    print " -h, --help :              Shows help menu"
    print " -v  --version :           Prints the version of vacation.py and exits"

########################################################################################################################

def addUsage():
    print "add option Usage:"
    print
    print " --add [email] [username] [message]"
    print
    print "[username]: is a unique name for one user"
    print "[email]: user e-mail address"
    print "[message] is the body of the autoreply message. if none is provided a default message is used"
   

########################################################################################################################

def removeUsage():
    print "remove option Usage:"
    print
    print " --remove [email]"
    print
    print "N.B: if a user own more than one e-mail address use [email] unless you want get rid of everything related"
    print "to such user"


########################################################################################################################


def enableUsage():
    print "enable option Usage:"
    print
    print " --enable [email]"
    print
    print "enable autoresponding for the [email] account"


########################################################################################################################

def disableUsage():
    print "disable option Usage:"
    print
    print " --disable [email]"
    print
    print "disable autoresponding for the [email] account"

########################################################################################################################

def deliverUsage():
    print "deliver option Usage:"
    print
    print " --deliver [sender] [recipient]"
    print
    print "deliver a reply message to the [sender] and his message to the [recipient]."
    print "This function get the input e-mail from stdin."

########################################################################################################################

def fileUsage():
    print "deliver option Usage:"
    print
    print " --file [email] [full_path]"
    print
    print "set the file content as the body of the autoreply e-mail for that [email] account"
    print "[full_path] path to the file wich contains the reply message text (file extension included)"

########################################################################################################################
# submenus selection

def chooseUsage(opt):
    if 'add' in opt:
        addUsage()
    elif 'remove' in opt:
        removeUsage()
    elif 'enable' in opt:
        enableUsage()
    elif 'disable' in opt:
        disableUsage()
    elif 'deliver' in opt:
        deliverUsage()
    elif 'file' in opt:
        fileUsage()
    else :
        usage()
 


#######################################################################################################################
# Connect to the databases

def dbConnect():
    try:
        global db
        db = sqlite.connect(dbname)

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)       
 
#######################################################################################################################
# Disconnect from the databases

def dbDisconnect():
    try:
        db.close()

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)
   
#######################################################################################################################
# check if a user already was inserted into the database; it returns weither true or false
# Input: user's email

def userExists(searchmail):
    try:
        #query = "select email from localUsers where email='%s'" % searchmail
        cur = db.cursor()
        cur.execute("select email from localUsers where email=%s" , searchmail)
        if cur.fetchone():
           cur.close()
           return True
        else :
           cur.close()   
           return False

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)
        
    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)

        
#######################################################################################################################
# Add a new user into the db
# Input type: string 

def addUser(email, name , message=None):
    try:
        # if no reply message content was provided fallback to default message
        if message is None:
           message = ""
           file = open(defaultmsgPath , 'r')
           for line in file:
               message += line
           file.close()

        # execute the query
        cur = db.cursor()
        cur.execute("insert into localUsers(email , name , message ) values ( %s , %s , %s )" , (email, name, message))
           
        # save the changes
        db.commit()
        cur.close()

    except sqlite.Error, e:
           print >> sys.stderr, "Error : %s" % e.args[0]
           logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
           sys.exit(1)

    except :
           print "Unexpected error:" , sys.exc_info()[0]
           logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
           sys.exit(1) 
    
#######################################################################################################################
# Add a new alias into the virtual alias db for postfix
# Input : user's email (string) 

def addAlias( email ):
        try:
            # check if an alias for this email already exists
            found = False
            file = open(virtualpath , 'r')
            for line in file:
                if line.find(email) != -1:
                   # The virtual address already exists
                   found = True
                   break
             
            file.close()

            if not found :
            # parse the email address in order to query the db
               tokens = string.split(email, "@")
               newentry = email + "\t\t" + email + "\t" + tokens[0] + "@" + "autoreply." + tokens[1] + "\n"

               virtual = open(virtualpath , 'a')
               virtual.write(newentry)
               virtual.close()
  
               os.system(postmap + " " + virtualpath)

        except IOError, e:
            print >> sys.stderr, "Error : %s" % e.args[0]
            logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
            sys.exit(1)

        except :
            print "Unexpected error:" , sys.exc_info()[0]
            logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
            sys.exit(1)


#######################################################################################################################
# Remove an alias from the virtual alias db for postfix
# Input: user's email (string)

def removeAlias(email):
        try:
            # read every configuration entry.
            # Do a match with the email for every line and write it to the file.
            # If it match it doesn't write it on the refreshed file   
            virtual = ""
            file = open(virtualpath , 'r')
            for line in file:
                if line.find(email):
                   virtual += line
             
            file.close()
            newfile = open(virtualpath , 'w')
            newfile.write(virtual)
            newfile.close()           

            os.system(postmap + " " + virtualpath)

        except IOError, e:
            print >> sys.stderr, "Error : %s" % e.args[0]
            logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
            sys.exit(1)

        except :
            print "Unexpected error:" , sys.exc_info()[0]
            logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
            sys.exit(1)


#######################################################################################################################
# Remove a user from the db. 
# Input: user's id (integer)

def removeUser(id):
        try:

            #deleteUserQuery = "delete from localUsers where id=%s" % id
            #deleteReplyQuery = "delete from replyList where id=%s" % id
            
            cur = db.cursor()
            cur.execute("delete from localUsers where id=%s" , id ) 
            cur.execute("delete from replyList where id=%s" , id )
            
            # save the changes
            db.commit()
            cur.close()

        except sqlite.Error, e:
            print >> sys.stderr, "Error : %s" % e.args[0]
            logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
            sys.exit(1)

        except :
            print "Unexpected error:" , sys.exc_info()[0]
            logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
            sys.exit(1)

     
#######################################################################################################################
# update user data 

def updateUser(id , message , email=None , name=None):
    try:
        cur = db.cursor()
        if email is None or name is None :
           cur.execute("update localUsers set  message=%s where id=%s" , ( message , id))
           
        else :
           cur.execute("update localUsers set email=%s , name=%s , message=%s where id=%s" , (email , name , message , id))

 
        db.commit()
        cur.close()

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)


#######################################################################################################################
# Enable autoreply for a user
# Input : user' id (integer)

def enable(id):
    try:
        # create query strings
        #updateQuery =  "update localUsers set vacation=1 where id=%s" % id
        #deleteQuery =  "delete from replyList where id=%s" % id

        cur = db.cursor()
        cur.execute("update localUsers set vacation=1 where id=%s" , id)
        cur.execute("delete from replyList where id=%s" , id)
        
        db.commit()
        cur.close()

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)


#######################################################################################################################
# Check if the sender of an email has been already replied by the autoreponder
# Input : sender's email (string)

def isActive(email):
    try:
        #query = "select email from localUsers where email='%s'" % email
        cur = db.cursor()
        cur.execute("select email from localUsers where email=%s" , email )
        
        query = cur.fetchone()
        cur.close()
        if query:
           return True
        else :
           return False
        
    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)


#######################################################################################################################
# Disable autoreply for a user
# Input : user' id (integer)

def disable(id):
    try:
        #query = "update localUsers set vacation=0 where id=%s" % id
        cur = db.cursor()
        cur.execute("update localUsers set vacation=0 where id=%s" , id )

        db.commit()
        cur.close()

    except sqlite.Error, e:
       print >> sys.stderr, "Error : %s" % e.args[0]
       logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
       sys.exit(1)

    except :
       print "Unexpected error:" , sys.exc_info()[0]
       logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
       sys.exit(1)


#######################################################################################################################
# Return the ID of a user
# input : user's email (string) 

def getID(email):
    try:
        # parse the email address in order to query the db
        tokens = string.split(email, "@")
        usermail = tokens[0] + "@" + domainame


        #query = "select id from localUsers where email='%s'" % usermail
        cur = db.cursor()
        cur.execute("select id from localUsers where email=%s" , usermail )
 
        id = cur.fetchone()[0]
        cur.close()

        return id

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )

        return False    

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        return False

#######################################################################################################################
# Return True if the sender doesn't appear into the replied list db and he's neither himself nor no_reply
# input : user's email

def isValidSender(  semail , uemail ):
    try:
        noreply = "no_reply@" + domainame
       
        if semail == uemail or semail == noreply :
           return False 
         
        #query = "select * from replyList where email='%s' AND id=%s" % ( semail , getID(uemail) )
        cur = db.cursor()
        cur.execute("select * from replyList where email=%s AND id=%s" , ( semail , getID(uemail)))
        if cur.fetchone():
           cur.close()
           return False
        else :
           cur.close()
           return True

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )

        return False    

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        return False

#######################################################################################################################
# check if the incoming email is what we are expecting . tags is a TUPLE

def isValidEmail(tags , inmail):
    try:
       # split the email in a list of lines
       lines = inmail.splitlines()   

       # compare any "tag" with the starting chunk of a line 
       for cur in range(0 , len(lines)) :
           # since python 2.5.* accept tuple with startswith either
           #if lines[cur].startswith(tags):
              #return False       

           # python 2.4 (but slower)
           for i in range(0 , len(tags)) :
               if lines[cur][0:len(tags[i])] == tags[i]:
                  return False
       return True
              
    except : 
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)


#######################################################################################################################
## Check if a local user is real

def isLocalUser(email) : 
    try:
        # parse the email address in order to query the db                                                                                                  
        tokens = string.split(email, "@")

        if tokens[1] == domainame :
           checkcmd = "grep -q '" + tokens[0] + "' /etc/passwd"
           ret = os.system(checkcmd)
           if ret == 0 :
              return True
        return False

    except:
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)
           

#######################################################################################################################
# Compose a reply message and deliver it to the sender 

def sendReply(replyrec , recipient ):
    try:

        sender = 'NO REPLY <no_reply@your-domain>'
        
        # compose the header of the reply message
        message = ( "From: %s\r\nTo: %s\r\n" % (sender, replyrec) )
        message += ( 'Subject: Out of office autoreply\r\n\r\n' )

        # parse the email address in order to query the db
        tokens = string.split(recipient, "@")
        usermail = tokens[0] + "@" + domainame

        #query = "select message from localUsers where email='%s'" % usermail
                 
        cur = db.cursor()
        cur.execute("select message from localUsers where email=%s" , usermail) 
        body = cur.fetchone()[0]
   
        # If we inserted the autoreply message via the command line it must clean it
        # removing escaping
        bodytmp = string.split(body, "\\n")
        i = 0
        for i in range(len(bodytmp)):
            message += bodytmp[i]
            message += "\r\n"
            i += 1

        # connect to the smtp server and send message
        server = smtplib.SMTP('localhost')
        #server.set_debuglevel(1)
        smtpresult = server.sendmail(sender, replyrec , message)
        server.quit()

    except sqlite.Error , e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)
         

#######################################################################################################################
# Send a confirmation mail

def notificationMail(recipient , type , msg=None):
   try:
        sender = 'NO REPLY <no_reply@your-domain>'
        
        # compose the header of the reply message
        message = ( "From: %s\r\nTo: %s\r\n" % (sender, recipient) )
     
        # notification management 
        if type == "success" :
           if msg is None :
              message += ( 'Subject: Autoreply daemon: command execution success!\r\n\r\n' )
              message += "Command executed correctly for: " + recipient + ".\n"
           else :
              message += ( 'Subject: Autoreply daemon: command execution success!\r\n\r\n' )
              message += "Command executed correctly for: " + recipient + ".\n"
              message += msg
        elif type == "warning" :
              message += ( 'Subject: Autoreply daemon: warning!\r\n\r\n' )
              message += msg
        else : 
           if msg is None :
              message += ( 'Subject: Autoreply daemon: command execution error!\r\n\r\n' )
              message += "Check that the syntax is correct\n"
              message += "********************************\n"
              message += "Send to <autoreply@your-domain>\n"
              message += "with the following syntax :\n"
              message += "autoreply: enable/disable\n\n"
              message += "and/or\n\n"
              message += "autoreply_message: your_autoreply_message"
              message += "\n\n"
              message += "If you wish to Subscribe/Unsubscribe use this:\n"
              message += "Subscribe: username\n\n"
              message += "or\n\n"
              message += "Unsubscribe:"
           else :
              message += ( 'Subject: Autoreply daemon: command execution error!\r\n\r\n' )
              message += msg


           
        server = smtplib.SMTP('localhost')
        smtpresult = server.sendmail(sender, recipient , message)
        server.quit()


   except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )


#######################################################################################################################
# Reinject mail into the mail server queue via sendmail

def sendLocal(sender , recipient , msg):
    try:
        MAIL = "/usr/sbin/sendmail"
        p = os.popen("%s -t" % MAIL , 'w')
        p.write(msg)
        smtpresult = p.close()

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)

        
#######################################################################################################################
# This function read the email from stdin

def getMail():
    try:
       email = ""
       for line in sys.stdin:
           email += line
       return email

    except IOError , e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Input/Output Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)

#######################################################################################################################
# Parse an email and return the appropriate command

def processMail(inmail , sender ):
    try:
       # patterns
       matchFrom = re.compile("^From:(.*)@(.*) " , re.IGNORECASE | re.MULTILINE )
       matchActivation = re.compile("^autoreply:(.*)" , re.IGNORECASE | re.MULTILINE )
       matchSub = re.compile("^Subscribe: (.*)" , re.IGNORECASE | re.MULTILINE )
       matchUnSub = re.compile("^Unsubscribe:" , re.IGNORECASE | re.MULTILINE )

       # get the sender email address
       """search_from = matchFrom.search(inmail)
       if search_from:
          ffrom = search_from.group(1) + "@" + search_from.group(2)

          # remove unuseful chars
          ffrom = ffrom.strip()
          ffrom = ffrom.strip('"')"""
       ffrom = sender
       
       # do patterns matching, produce a match object
       searchActivation = matchActivation.search(inmail)
       searchSub = matchSub.search(inmail)
       searchUnSub = matchUnSub.search(inmail)

       # notification flag set to failure and Details to Null object
       ntype = "failure"
       msgDetail = None
    
       # activation
       if searchActivation :
          activation = searchActivation.group(1)
          activation = activation.strip()
          if activation == "enable" :
             if userExists(ffrom):
                enable(getID(ffrom))
                addAlias(ffrom)
                ntype = "success"
                msgDetail = "Autoreply enabled"
                
                index = inmail.find("autoreply_message:")
                # if it succeds index is >= 0
                if index != -1 :
                   bodymessage = inmail[index+len("autoreply_message:"):]
                   updateUser(id=getID(ffrom) , message=bodymessage )
                   ntype = "success"
                   msgDetail = "Autoreply enabled\nYour message is:\n" + bodymessage
        
          elif activation == "disable" :
               if userExists(ffrom):
                  disable(getID(ffrom))
                  removeAlias(ffrom)
                  ntype = "success"
                  msgDetail = "Autoreply disabled"
          
       
       # subscription
       elif searchSub :
          uname = searchSub.group(1)
          uname = uname.strip()
                    
          # check if input chars are right....TODO
          if not userExists(ffrom) and isLocalUser(ffrom):
             addUser( ffrom, uname )
             ntype = "success"
             msgDetail = ffrom + " subscribed with the username: " + uname
          else :
             ntype = "warning"
             msgDetail = "\n" + ffrom + " already exists or is not a valid address: command not executed"

       elif searchUnSub :
          # check if input chars are right....TODO
          if userExists(ffrom) and isLocalUser(ffrom):
             removeUser(getID(ffrom))          
             removeAlias(ffrom)
             ntype = "success"
             msgDetail = ffrom + " unsubscribed"
          else :
             ntype = "warning"
             msgDetail = "\n" + ffrom + " does not exists or is not a valid address : command not executed"
          
       # message update
       index = inmail.find("autoreply_message:")
       if index != -1 and userExists(ffrom) :
          bodymessage = inmail[index+len("autoreply_message:"):]
          updateUser(id=getID(ffrom) , message=bodymessage )
          ntype = "success"
          msgDetail =  "Your new reply message is:\n" + bodymessage       

       # notification
       notificationMail(ffrom , ntype , msgDetail)
                            
    except:
         notificationMail(ffrom , "failure" )
         print "Unexpected error:" , sys.exc_info()[0]
         logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
         sys.exit(1)

#######################################################################################################################
# adds a new sender entry for a user  

def addToReplyList(sender , recipient):
    try:
        # set the user ID corresponding to the provided email address
        ID = getID(recipient)
        
        #query = "insert into replyList(id , email) values ( %s , '%s' )" % (ID , sender)
         
        cur = db.cursor()
        cur.execute("insert into replyList(id , email) values ( %s , %s )" , (ID , sender))

        db.commit()
        cur.close()

    except sqlite.Error, e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )

    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )

#######################################################################################################################
# get the reply message's body from a text file

def loadBodyFile(email , path):
    try:
        # read the content from file
        bodyFile = path
        file = open( bodyFile, 'r' )
        bodyMes = ""
        for line in file:
            bodyMes += line
        file.close()

        #query = "update localUsers set message='%s' where email='%s'" % (bodyMes , email)
        # put the new content into the database
        cur = db.cursor()
        cur.execute("update localUsers set message=%s where email=%s" , (bodyMes , email))
 
        db.commit()
        cur.close()
        
    except IOError , e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("I/O Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)

    except sqlite.Error , e:
        print >> sys.stderr, "Error : %s" % e.args[0]
        logging.error("Database Error: %s in function: " + whoami() , e.args[0] )
        sys.exit(1)


    except :
        print "Unexpected error:" , sys.exc_info()[0]
        logging.error("Unknown Error: %s in function: " + whoami() , sys.exc_info()[0] )
        sys.exit(1)

#######################################################################################################################
############################################## MAIN ###################################################################
#######################################################################################################################

if __name__ == '__main__':
    try:
        (opts, getopts) = getopt.getopt(sys.argv[1:] , "uvh?a:r:e:d:A:D:u" , 
                          ["add=", "remove=", "enable=", "disable=", "use=", "verbose", "help", "deliver=" , "file=", "update=", "autoreply="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err)
        usage()
        sys.exit(2)

    # connect to the database
    dbConnect()

    # i want to check argument passing integrity
    if len(getopts) == 1 :
       arg1 = getopts[0]
       arg2 = ""
    elif len(getopts) == 2 :
         arg1 = getopts[0]
         arg2 = getopts[1]
    else : 
         arg1 = ""
         arg2 = ""

    for opt, arg in opts:
        if opt in ('-h', '-?', '--help'):
            usage()
        if opt in ('-a', '--add'):
            if not userExists(arg):
               addUser( arg , arg1 , arg2 )
        if opt in ('-r', '--remove'):
            if userExists(arg):
               removeUser(getID(arg))
               removeAlias(arg)   
        if opt in ('-e', '--enable'):
            if userExists(arg):
               enable(getID(arg))
               addAlias(arg)   
        if opt in ('-d', '--disable'):
            if userExists(arg):
               disable(getID(arg))
               removeAlias(arg)   
        if opt in ('-u', '--use'):
            chooseUsage(opts[0])
        if opt in ('--deliver' , '-D'):
            if isValidSender(arg , arg1) and isValidEmail(listsTag , getMail()):
               sendReply(arg , arg1)
               addToReplyList(arg , arg1)
        if opt in ('--autoreply' , '-A'):
            processMail(getMail() , arg)
        if opt in ('--file' , '-f'): 
            if userExists(arg):
               loadBodyFile(arg , arg1)
        if opt in ('--update' , '-u'): 
            if userExists(arg):
               updateUser(getID(arg), arg , arg1 , arg2)


# disconnection from the database
    dbDisconnect()
    sys.exit(0)
