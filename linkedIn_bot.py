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
        self.time_visited = 0
        self.relations = 0
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
        
        #TODO Lancement de la recuperation de la visibilite de mon profile
        driver = self.get_my_dashboard(driver,'/feed/')
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
            
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(PAUSE_TO_SCROLL)
            nouveau_scroll = driver.execute_script("return document.body.scrollHeight")
            if(nouveau_scroll == dernier_scroll):
                break
            dernier_scroll = nouveau_scroll
            n +=1
        logger.info("Scroll Down %d time" % n)
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
        #print(recommends)
        logger.info("%d profile to visit "%len(recommends))
        print(len(recommends))
        logger.info("Profile a explorer %d"%len(recommends))
        for recommend in recommends:
            url = self.base_url + recommend['href']
            username = recommend.select('span.discover-person-card__name.t-16.t-black.t-bold')[0].text.strip()
            fonction = recommend.select('span.discover-person-card__occupation.t-14.t-black--light.t-normal')[0].text.strip()
            if not username in open(self.visited_file).read():
                driver.get(url)
                logger.info("Profile visited %s"%username)
            else :
                print(username+" already visited")
            self.write_in_resultat_file(username+" : "+fonction+" -> "+url)
            time.sleep(TEMPORISATION)
        logger.info("Grow visibiliy ended")
        return driver
        
    def get_my_dashboard(self,driver,suffixe_url):
        """
        Recuperation des informations sur mon profile
        Combien de personnes ont consulté mon profile
        Combien d'apparition dans les resultats de recherche
        Combien on vue mes articles
        """
        print("Recuperation des stats")
        logger.info("get my profile data")
        driver.get(self.base_url+suffixe_url)
        soup= BeautifulSoup(driver.page_source,"lxml")
        visited_time=soup.select('span.feed-identity-module__stat.link-without-visited-state')
        self.time_visited = int(visited_time[0].text.strip())
        self.relations=int(visited_time[1].text.strip())
        print(self)
        logger.info("nombre de fois ou mon profile a ete visite %s"%visited_time[0].text.strip())
        logger.info("nombre de relations %s"%visited_time[1].text.strip())
        return driver

    def write_in_resultat_file(self,res):
        f = open(self.visited_file,"a+")
        if type(res) is str:
            f.write(res+"\n")
        if type(res) is bytes:
            f.write(res.decode("utf-8")+"\n")
        f.close()
    
    def bot_stats(self):
        num_lines = sum(1 for line in open(self.visited_file))
        logger.info("Bot a visiter %d profiles a ce jour "%num_lines)
                
    def __str__(self):
        return "baseurl:{} | config file:{} | Account{} | Scroll_Down:{} | Profile visited {} times, and you have {} relations".format(self.base_url,self.config,self.linkedin_id,self.n_scroll_down, self.time_visited,self.relations)


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
    bot.bot_stats()