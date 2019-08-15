##IMPORT
import os, random, sys, time
import argparse

from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
from termcolor import colored, cprint # Colorama library is also good for terminal color

import pyAesCrypt

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')   
file_handler = RotatingFileHandler('log\\activity.log','a',1000000,10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

class Bot:
    """Robot linkedIn"""
    
    def __init__(self,config,password,n_scroll_down=5):
        self.choice = 0
        self.base_url = 'https://linkedin.com'
        self.config = config
        self.password = password
        self.linkedin_id = ""
        self.linkedin_pass = ""
        self.visited_file='visited.txt'
        self.bufferSize = 64 * 1024
        self.n_scroll_down = n_scroll_down
        self.initialisation_logger()
        self.check_configfile()
        self.check_visited_users_file()
    
    def initialisation_logger(self):
        """Initilisation du logger pour l'inscription dans les logs"""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')   
        file_handler = RotatingFileHandler('log\\activity.log','a',1000000,10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.warning("Lancement du bot")
        
    def check_configfile(self):
        """
        Verification de l'existance du fichier de configuration
        si fichier en clair => recuperer username et password + crypter + remove du fichier en clair
        si fichier crypter => decrypter et recuperer username et password et remove fichier clair
        """
        if not os.path.isfile(self.config):
            if not os.path.isfile(self.config + ".aes"):
                print("Pas de fichier de configuration dans le repertoire courant")
                print("Veuillez enregistrer vos identifiant dans un fichier")
                print("Lors de la prochaine execution utiliser les argument --config et --password ou --help")
                sys.exit()
        if os.path.isfile(self.config):
            if os.path.isfile(self.config+".aes"):
                logger.info("Ancien fichier crypté existant")
                os.remove(self.config+".aes")
                logger.remove("Suppression de l'ancien fichier crypter")
            # Get Authentication data
            logger.info("Fichier config existant")
            file = open(self.config,'rb')
            self.linkedin_id = file.readline().strip()
            self.linkedin_pass = file.readline()
            file.close()
            # Crypte config file
            logger.info("Recuperation des données d'authentification'")
            pyAesCrypt.encryptFile(self.config,self.config+".aes",self.password,self.bufferSize)
            logger.info("Cryptage du fichier")
            # delete config file
            os.remove(str(self.config))
            logger.info("Suppression du fichier clair")

        if os.path.isfile(self.config+".aes"):
            # Decrypte file
            logger.info("Fichier crypter existant")
            pyAesCrypt.decryptFile(self.config+".aes",self.config,self.password,self.bufferSize)
            logger.info("Decryptage du fichier de configuration")
            # Get Authentication data
            file = open(self.config,'rb')
            self.linkedin_id = file.readline()
            self.linkedin_pass = file.readline()
            logger.info("Récuperation des identifiant de connection")
            file.close()
            # delete config file
            os.remove(str(self.config))
            logger.info("Suppression du fichier clair")
    
    def check_visited_users_file(self):
        """
        Verification de l'existance du fichier visited.txt
        si fichier non présent le créer
        """
        if not os.path.isfile(self.visited_file):
            file = open(self.visited_file,'wb')
            file.close()
    
    def open_browser(self):
        """
        Overture du navigateur
        Authentification
        Connection
        """
        options = Options()
        options.binary_location="D:\Tools\GoogleChromePortable\App\Chrome-bin\chrome.exe"
        driver = webdriver.Chrome(chrome_options=options,executable_path='chromedriver.exe')
        logger.info("Connection à Linkedin")
        driver.get(self.base_url)
        emailElement = driver.find_element_by_name('session_key')
        emailElement.send_keys(self.linkedin_id.decode('utf-8').strip())
        passElement = driver.find_element_by_name('session_password')
        passElement.send_keys(self.linkedin_pass.decode('utf-8').strip())
        logger.info("Saisie des identifiants")
        logger.info("Tentative d'Authentification")
        passElement.submit()
        soup = BeautifulSoup(driver.page_source,"html5lib")
        print(soup.find('label',text='Mot de passe'))
        if soup.find('label',text='Mot de passe'):
            logger.error("Erreur d'Authentification! Merci de verifier vos identifiants.")
            driver.close()
        elif driver.title == '403: Forbidden':
            logger.error('LinkedIn est momentanement indisponible. Merci de refaire une tentative plutart.')
            driver.close()
        else:
            logger.info("Tentative de connection resussie")
        
        driver = self.grow_visibility(driver,'/mynetwork/')
        driver.close()
        
    def scroll_down_n_time(self,driver):
        """
        Descendre en bas de page n fois 
        """
        PAUSE_TO_SCROLL=1
        dernier_scroll = driver.execute_script("return document.body.scrollHeight")
        n=1
        
        while n < self.n_scroll_down:
            logger.info("Scroll Down %d" % n)
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(PAUSE_TO_SCROLL)
            nouveau_scroll = driver.execute_script("return document.body.scrollHeight")
            if(nouveau_scroll == dernier_scroll):
                break
            dernier_scroll = nouveau_scroll
            n +=1
        return driver
    
    def grow_visibility(self,driver,suffixe_url):
        """
        Visiter plusieurs profile pour augmenter ma visibilite
        """
        TEMPORISATION = 4
        driver.get(self.base_url+suffixe_url)
        driver = self.scroll_down_n_time(driver)
        soup = BeautifulSoup(driver.page_source,"lxml")
        #recommends = soup.findAll('a',{'class':'discover-person-card__link ember-view'})
        recommends = soup.select('a.discover-person-card__link.ember-view')
        print(recommends)
        print(len(recommends))
        logger.info("Profile a explorer %d"%len(recommends))
        for recommend in recommends:
            url = self.base_url + recommend['href']
            driver.get(url)
            print(recommend)
            logger.info("Url Visited %s"%url)
            time.sleep(TEMPORISATION)
        logger.info("Grow visibiliy ended")
        return driver
    
                
    def __str__(self):
        return "baseurl:{}| config file:{}| password:{}| linkedin_id:{}| linkedin_pass:{}|  Scroll_Down:{}".format(self.base_url,self.config,self.password,self.linkedin_id,self.linkedin_pass,self.n_scroll_down)


##MAIN
if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='Visiter les profiles recommendé')
    parser.add_argument('-c','--config',help='fichier de configuration contenant email et mot de passe',type=str)
    parser.add_argument('-p','--password',help='mot de passe pour decrypter le fichier de configuration')
    parser.add_argument('-s','--scrolldown',type=int,help='nombre de pages a afficher par scroll down')
    
    args = parser.parse_args()
    
    bot = Bot(args.config,args.password,args.scrolldown)
    #print(bot)
    bot.open_browser()