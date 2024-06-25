# Food Review System

### This project was developed as the final requirement for CMSC 127.

Developers:
1. M. Alarcon
2. J. Manalo
3. A. Mapute

### This file contains the prerequisites, codes, packages, and instructions on how to run the application. The zip file also already contains the .sql setup file. 

Requirements:
1. python (https://www.python.org/downloads/)
2. mariadb (https://mariadb.com/downloads/)

Steps on how to run the application:
1. install python, mariadb, and pip 
2. log in to your mariadb root account
3. source the file: project.sql
4. enter the application directory
5. install tk and mysql-connector-python through pip in the console
    -- pip install tk
    -- pip install mysql-connector-python
6. make a file named config.py and add the line:
    -- password = ""
7. add your root password set in mariadb inside the quotation marks in config.py
8. save the config.py and run the file: app.py