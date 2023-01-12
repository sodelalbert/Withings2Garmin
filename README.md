# Withings2Garmin

This project allow you to sync your measurements between Withings scale and Garmin Connect to have unified experience.

## Preconditions

## Installation

Clone repository from GitHub

```
git clone https://github.com/sodelalbert/Withings2Garmin.git
```
Insert your Garmin Connect password into file ``` config/secret.json``` as in example:

``` 
{
"user": "john.rambo@thepool.com",
"password": "firstblood"
}
``` 

Passwords are stored locally inside your host operating system. Make sure that they are not accesible from the network. 

## Initial run



It's required to perform first run manually. During that you will need to chose user of of the scale and ``` config/withings_user.json``` will be created automatically for authorization purposes.

Please add execution rights to ```run.sh```
```
chmod +x run.sh
```

Perform initial config.

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

Copy token from web page and copy into terminal and press Enter. Output should look like this 
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

Your measurements should be synchornized at this point ;) 

## Manual synchronization

Script sync.py allows to use command line arguments. By default it will synchronize your reporst starting from 2022-01-01 up to current date. 

```./sync```

If you would like to specidy manualy  range you can do it by executing following command.

```./sync -fromdate --fromdate 2022-01-01 --todate 2022-01-10```


## References

Thanks to jaroslawhartman for sharing code of withings-garmin-v2. This app is based on his briliant project.
