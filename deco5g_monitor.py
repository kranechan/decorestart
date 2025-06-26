import time
import socket
import logging
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#parameter 
start_time = time.time()
pw = ''
REMOTE_SERVER = "one.one.one.one"

#logging setup and configuration
logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s",
    level = logging.INFO,
    handlers=[
        logging.FileHandler("event.log"),
        logging.StreamHandler(),
    ])

#obtain password    
with open('/home/pi/cred.txt','r')as f:
	pw = f.readline().strip()

#setup webdriver to be headless
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('start-maximized')

#convert seconds to days, hours, minutes, seconds
def normalize_seconds(seconds):
    days = divmod(seconds, 86400) 
    # days[0] = whole days and
    # days[1] = seconds remaining after those days
    hours = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)
    return "%i days, %i hours, %i minutes, %i seconds" % (days[0], hours[0], minutes[0], minutes[1])

#test connection function using socket
def is_connected(hostname):
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, 80),2)
        s.close()
        return True
    except Exception:
        pass
    return False

#restart router using selenium automation
def restart_router():
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('http://192.168.1.1/webpages/index.html#reboot')
    wait = WebDriverWait(driver, 60)

	#login to TPlink Deco page
    wait.until(EC.visibility_of_element_located((By.ID, "local-login-pwd")))
    driver.find_element(By.XPATH, "//input[@class='text-text password-text password-hidden  ']").send_keys(pw)
    driver.find_element(By.ID, 'local-login-button').click()
    wait.until(EC.visibility_of_element_located((By.ID, "reboot-view")))
	
	#Scroll to the reboot all button and reboot
    element_rebootbutton = driver.find_element(By.XPATH, "//div[@id='reboot-button']")
    driver.execute_script("arguments[0].scrollIntoView(true);", element_rebootbutton)
    driver.find_element(By.ID, 'reboot-button').click()
    wait.until(EC.element_to_be_clickable((By.ID, "global-confirm-btn-ok"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "reboot-msg")))
    driver.quit()
    
    #Ensure the router connected to internet
    while(True):
        time.sleep(5)
        if(is_connected(REMOTE_SERVER))==1:
            logging.info("Restart completed")
            break

#Main thread where the process of checking is done here
while(True):
    try:
        if(is_connected(REMOTE_SERVER))==0:
            elapsed = time.time()-start_time
            elapsed = normalize_seconds(elapsed)
            logging.info('Total Uptime: {}'.format(elapsed))
            restart_router()
            start_time = time.time()
    except:
        logging.info("Error post connection check")
    
    time.sleep(random.randint(10,61))
