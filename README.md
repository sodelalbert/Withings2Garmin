# Withings2Garmin

This project allow you to sync your measurements between Withings scale and Garmin Connect to have unified experience.

## Preconditions

## Installation

Clone repository from GitHub

```
git clone https://github.com/sodelalbert/Withings2Garmin.git
```
Inser your Garmin Connect password into file ``` config/secret.json``` in example:

``` 
{
"user": "john.rambo@thepool.com",
"password": "firstblood"
}
``` 

Passwords are stored locally inside your host operating system. Make sure that they are not accesible from the network. 

## Initial run

It's required to perform first run manually. During that you will need to chose user of of the scale and ``` config/withings_user.json``` will be created automatically for authorization purposes .
```
❯ ./sync.py
Can't read config file config/withings_user.json
***************************************
*         W A R N I N G               *
***************************************

User interaction needed to get Authentification Code from Withings!

Open the following URL in your web browser and copy back the token. You will have *30 seconds* before the token expires. HURRY UP!
(This is one-time activity)

https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=183e03e1f363110b3551f96765c98c10e8f1aa647a37067a1cb64bbbaf491626&state=OK&scope=user.metrics&redirect_uri=https://wieloryb.uk.to/withings/withings.html&

Token :  
```

Copy token from web page and copy into terminal and press Enter. Terminal output should look like this 
```
❯ ./sync.py
Can't read config file config/withings_user.json
***************************************
*         W A R N I N G               *
***************************************

User interaction needed to get Authentification Code from Withings!

Open the following URL in your web browser and copy back the token. You will have *30 seconds* before the token expires. HURRY UP!
(This is one-time activity)

https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=183ef03e1f363110bd551f96765c98c10e8f1aa647a37067a1cb64bbbaf491626&state=OK&scope=user.metrics&redirect_uri=https://wieloryb.uk.to/withings/withings.html&

Token : c6487a2sdde7d8f5bf0ceab702aee5f655e70dc4
Withings: Get Access Token
Withings: Refresh Access Token
Withings: Get Measurements
   Measurements received
3e7cc8d8-c9ed-40f4-98ec-28539ec6afc0
Garmin Connect User Name: 3efa8d8-c9ed-40f4-98ec-21259ec6afc0
Fit file uploaded to Garmin Connect
```


## Automated sync

Now you can utilize crontab as scheduler of script runs. It will allow to synchronize your measurements and you can forget about the script. In below exaple Raspberry Pi was used as server.

Execute ```crontab -e```

```
 */5 * * * * /home/pi/Withings2Garmin/run.sh >> /home/pi/cron.log 2>&1
```

This approach allows simple loging to ```/home/pi/cron.log``` directory. 

```
Sun 12 Jan 2020 02:25:01 PM CET
Garmin Connect User Name: 3e7cc8d8-c9fd-40f4-98ec-28539ec6afc0
Withings: Refresh Access Token
Withings: Get Measurements
   Measurements received
3e7cc8d8-c9ed-4ff4-98ec-28539ec6afc0
Fit file uploaded to Garmin Connect
----------------------------------------
```


## References

Thanks to jaroslawhartman for sharing code of withings-garmin-v2. This app is based on his briliant project.
