pyvacation
==========

Postfix python autoresponder

Pyvacation is a simple python autoresponder for the Postfix Mail Server.

# INSTALLATION

1. Copy pyvacation into Postfix configuration 

~# mkdir /etc/postfix/autorespoder
~# cp pyvacation.py /etc/postfix/autoresponder/

2a.

~# vim /etc/postfix/master.cf 
#add these lines
autoreply       unix    -       n       n       -       -       pipe
  flags= user=vacation argv=/etc/postfix/autoresponder/pyvacation.py --deliver ${sender} -- ${recipient}
autoreplyCmd       unix    -       n       n       -       -       pipe
  flags= user=vacation argv=/etc/postfix/autoresponder/pyvacation.py --autoreply ${sender} -- ${recipient}

2b.

~# vim /etc/postfix/main.cf

# uncomment or add this line
 transport_maps = hash:/etc/postfix/transport


# add autoreply_virtual to the virtual_alias_map lookup tables
 virtual_alias_maps = hash:/etc/postfix/virtual,
        hash:/etc/postfix/autoreply_virtual

3.
Add to /etc/postfix/virtual :

autoreply@moldiscovery.com              autoreply@autoreplyCmd.your-domain

4.
Add to /etc/postfix/transport :

autoreply.yourdomain     autoreply:
autoreplyCmd.yourdomain   autoreplyCmd:
gotreply.yourdomain       tracker_reply:

5.
Create the file "autoreply_virtual" in /etc/postfix 

~# touch /etc/postfix/autoreply_virtual

6. 
If you have SELINUX enabled you are needed to add a police for the 
autoresponder to work properly. I'm using this one:

module vacationpolicy 1.0;

require {
        type tmp_t;
        type postfix_pipe_t;
        type postfix_spool_t;
        type postfix_etc_t;
        type postfix_map_exec_t;
        class dir { write remove_name add_name read search };
        class file { write create unlink getattr append execute execute_no_trans read };
}

#============= postfix_pipe_t ==============
allow postfix_pipe_t postfix_spool_t:dir { write remove_name add_name };
allow postfix_pipe_t postfix_spool_t:file { create unlink };
allow postfix_pipe_t postfix_map_exec_t:file { execute getattr execute_no_trans read };
allow postfix_pipe_t tmp_t:dir { read write search add_name remove_name };
allow postfix_pipe_t tmp_t:file { create unlink getattr };
allow postfix_pipe_t postfix_etc_t:file { append write };

7. RELOAD POSTFIX CONFIGURATION

# USAGE

Activate/Deactivate autoreponder via email :
Send an email to autoreply@moldiscovery.com and put in its body the following commands:

#To Activate autoreply:
  autoreply: enable

#To deactivate autoreply:
  autoreply: disable

#To set your message:
  autoreply_message:

  I'll send an autoreply to the world
  I hope that someone gets my
  Message in an e-mail, yeah
  
  Sting

#You may want combine the enable option with your custom message; if so you can type:

  autoreply: enable 
  autoreply_message:

  I'll send an autoreply to the world
  I hope that someone gets my
  Message in an e-mail, yeah
  
  Sting

#Subscribe:
  Subscribe: username

#Unsubscribe:
  Unsubscribe:

N.B: COMMANDS ARE CASE SENSITIVE.
