Djails
======

An application designed to ban users. The application is plugged and gives the current User model a new feature: ban, unban, and check ban for users. Bans are accumulable and can be checked, reverted, forgiven, and expired.

Instructions
============

1.  Install "djails" in your project (i.e. add "djails" in the INSTALLED_APPS tuple).  
  
2.  If you have a custom User model, you can specify (in DJAILS_USER_CREATOR setting) a custom function that gets-or-creates a user based on a username. The default implementation looks like:

    ```
    def create_special_user(model_class, username):
    
        return model_class.objects.get_or_create(username=username, defaults={'email': unicode(username) + u'@example.com'}

    #It will install 3 users (currently __auto_ban__ is not used in the system).
    ```
  
3.  The service.DjailsService wrapper class allows you to:
    *   Check wether the user is banned or not.
    *   Ban another user.
    *   Forgive/Revert a ban.
  
This example is a how-to for this app:

      klass = get_user_model()  
      admin = klass.objects.get("someUser")  
      admin_wrapper = service.DjailsService(admin)  
      client = klass.objects.get("anotherUser")  
      client_wrapper = service.DjailsService(client)  
      new_ban = admin_wrapper.ban(client, "1d", "one-day sample ban")  
      current_ban = client_wrapper.my_current_ban()  
      assert new_ban == current_ban, "They must match"  
      dead_ban = admin_wrapper.forgive(new_ban, "forgiving sample ban")  
      #admin_wrapper.revert works as well, with same parameters  

4. You can wrap your views with class-based decorators that make your view behave differently depending on wether the current user in session is banned or not.  
These decorators, upon anonymous user or user being banned, process an alternative flow to the wrapped view.  

       from decorators import ifban, ifban_forbid, ifban_redirect, ifban_same  
       
       #You can subclass those decorators. You can override:  
       
       class my_ifban(ifban):  
           def on_anonymous(self, request, *args, **kwargs):  
               #return a response here  

        def on_banned(self, request, *args, **kwargs):  
               #return a response here  
    
       class my_ifban_redirect(ifban_redirect):  
           def on_anonymous(self, request, *args, **kwargs):
               #return a response here  
       
           def get_redirection(self, request, *args, **kwargs):  
               #return a (url, isPermanentRedirect:Boolean) tuple  
               #like ('/', True) being a Permanent Redirect to '/'.  
       
       class my_ifban_forbid(ifban_forbid):  
           def on_anonymous(self, request, *args, **kwargs):  
               #return a response here  
       
           def get_content(self, request, *args, **kwargs):  
               #return a (text, content-type name) tuple  
       
       class my_ifban_same(ifban_same):  
           def on_anonymous(self, request, *args, **kwargs):  
               #return a response here  
    
       #and instantiate them as: my_ifban(allow_anonymous, ban_attr_name='current_ban', service_attr_name='service', view_attr_name='view')  
       #   the 1st param will determine wether not being logged in or not "auth" installed will call the original view or the on_anonymous view.  
       #   the 2nd param will be the name of the request attribute holding the current ban (for the on_banned view).  
       #   the 3rd param will be the name of the request attribute holding the wrapped user (for the on_banned view, and the original view; may be None if allowed anonymous and no user is logged in).  
       #   the 4th param will be the name of the request attribute holding the wrapped view (for the on_banned view, and the on_anonymous view).  
    
       #finally, wrap views  
       @my_ifban(True)  
       def my_view(request, *args, **kwargs):  
           #return a response here.  

5. In djails.signals there are signals that react to user banning and ban termination.

       #in each case, the sender will be the banned user.  
       #  ban_applied: new_ban ()  
       #  ban_terminated: ban (the one that was terminated by an explicit call)  
       #  bans_expired: current_ban (if any), ban_list (expired ban list in the current call)  
    
       #use them with the usual @receiver decorator  
       @receiver(signals.bans_expired, dispatch_uid="example.unbanned")  
       def bans_expired_handler(sender, **kwargs):  
           #... handle  
           pass  
