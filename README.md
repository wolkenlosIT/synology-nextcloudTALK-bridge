# Synology to Nextcloud TALK bridge
This little python app will enable your Synology to send notifications to your desired Nextcloud talk room. You don´t need a nextcloud bot or another addon or plugin. Also, we will make use of webhook targets in stock Synology DSM. What I want to say is, all you need is a Synology, a nextcloud talk and an debian/ubuntu lxc/vm and you my friend are ready to rock!

## Requirements
* Synology DSM
* Nextcloud with Nextcloud Talk
* Debian or Ubuntu LXC/VM

## Setup
1. We will first prepare a service account with an app password on our nextcloud and add him to the targeted room
2. We will setup the python app and systemd service on the lxc/VM
3. We will configure the webhook target on synology
4. Optional: We will monitor the app via Uptime Kuma

### Nextcloud setup
1. Create a new user
2. If you don´t already have a nextcloud talk channel for your notifications, create one
3. Add the new user to the channel
4. Copy the channel id. To do so enter the channel. You just need to copy the last part of the url. For example if your url is *https://nextcloud.pizzaparty.lan/call/xvq3a88p* you need to copy the *xvq3a88p*
5. Logout and login as the new user
![NextcloudAPPtoken](https://github.com/wolkenlosIT/proxmox-nextcloudTALK-bridge/blob/main/setupimages/nextcloudapptoken.jpg)
6. Click on your profile pic ---> Click on Settings ---> Click on Security --> Scroll down to *Devices & sessions* and enter an App Name --> Click on *Generate new app password*
7. The popup will present you the password. Copy it. We will need it in the next step
8. Optional: If you want to add an avatar to the service account: Now is a good time to do so!
9. With this the setup on your nextcloud is completed

### Python app setup
1. Log into your debian or ubuntu lxc/vm with root or a sudo user
2. Let´s create the app first. Our working dictionary will be:
```shell
sudo mkdir /opt/synology-talk-bridge
```
3. Copy/past the app.py or download it to the directory. You don´t have to change anything here.
```shell
sudo nano /opt/synology-talk-bridge/app.py
```
5. Let´s create the webhook secret:
```shell
openssl rand -hex 16
```
6. Copy the secret and let´s create our environments file. Fill it out, too! Don´t change the port if you don´t know what you are doing!
```shell
sudo nano /etc/synology-talk-bridge.env
```
7. Let´s add a user, group and change the permission to our files, so that we can let the app run as a non root user:
```shell
sudo groupadd --system synology-talk
sudo useradd --system --gid synology-talk --home-dir /opt/synology-talk-bridge --shell /usr/sbin/nologin synology-talk
sudo chown -R synology-talk:synology-talk /opt/synology-talk-bridge
sudo chown root:synology-talk /etc/synology-talk-bridge.env
sudo chmod 640 /etc/synology-talk-bridge.env
```
8. The next step is the creation of a systemd service:
```shell
sudo nano /etc/systemd/system/synology-talk-bridge.service
```
9. Reload the deamon and enable the service for an autostart:
```shell
sudo systemctl daemon-reload
sudo systemctl enable synology-talk-bridge.service
```
10. You can now start the app via systemd and check the status:
```shell
sudo systemctl start synology-talk-bridge.service
sudo systemctl status synology-talk-bridge.service
```
11. You can check with the following if the webservice is reachable:
```shell
curl -i http://127.0.0.1:8789/health
```
12. With this. We can move to one of our synology servers!

### Synology setup
1. Log into your Synology and click on "Control Panel" and select "Notifications".
![Synologywebhooksetup1](https://github.com/wolkenlosIT/synology-nextcloudTALK-bridge/blob/main/setupimages/synology.jpg)
2. Then click on "Webhook" and "Add". Set "Custom" for "Provider" and "All" for "Rules. Then press "Next":
![Synologywebhooksetup2](https://github.com/wolkenlosIT/synology-nextcloudTALK-bridge/blob/main/setupimages/synology2.jpg)
3. For "Provider Name" enter whatever you want. Leave the Subject as is. For "Webhook URL" enter the following:
```shell
http://SWAP_WITH_YOUR_LXC_IP_ADRESS:8789/synology?text=%40%40TEXT%40%40
```
![Synologywebhooksetup3](https://github.com/wolkenlosIT/synology-nextcloudTALK-bridge/blob/main/setupimages/synology3.jpg)
7. Under "HTTP Method" select "POST". Add a Header under HTTP Header with the "parameter": X-Synology-Webhook-Secret and the value which is your webhook secret that you created before.
9. Add the following "HTTP Body" and press save:
```shell
{
  "title": "@@TITLE@@",
  "message": "@@TEXT@@"
}
```
![Synologywebhooksetup4](https://github.com/wolkenlosIT/synology-nextcloudTALK-bridge/blob/main/setupimages/synology4.jpg)
9. Select your Target and click on Test. If everything is working you should have received a message in your Nextcloud Talk room


### Monitor the bridge with Uptime Kuma
1. Log into your Uptime Kuma
2. Add a new monitor
3. For "Monitortyp" select "HTTP(s)"
4. For the "URL" http://SWAP_WITH_YOUR_LXC_IP_ADRESS:8788/health
5. Safe

##
I hope you like this! This is my second repo, so please give me advice!
You can ask me questions in German too!






