Dans le cadre de notre deuxième année de master Technologies numériques appliquées à l'histoire à l'Ecole nationale des chartes, nous avons développé une application python, 'Mise en registre !', présentant des documents médiévaux ayant été enregistrés par le parlement de Paris sous le règne de Louis XI.

# 👑 Mise en registre ! 👑 

## L'origine de l'application

📚 L'application a été créée dans le cadre de l'évaluation du cours python dispensé en seconde année de master Technologies numériques appliquées à l'histoire à l'Ecole nationale des chartes durant l'année 2020-2021.

Les données des documents évoquées ont été collectées par Anne Fleuret dans le cadre de son master de recherche en histoire médiévale à l'université Panthéon-Sorbonne. Elle nous permet gracieusement de les exploiter pour notre travail. Elle-même s'est appuyée sur le travail d'Henri Stein, chartiste, archiviste et historien, et plus particulièrement sur son inventaire des registres du parlement de Paris.📙


## Fonctionnalités

📜 	L'application présente les documents enregistrés par le parlement de Paris, c'est à dire copiés dans un registre. Chacun d'entre eux est renseigné par une notice. Les utilisateurs peuvent effectuer des recherches plein-texte parmi les regestes ou dans l'ensembles des données fournies. Ils peuvent également rechercher un type de document précis. Afin d'avoir une vue d'ensemble des documents enregistrés, ils peuvent également consulter les index.

Les données de l'application peuvent être modifiées et enrichies : pour ce faire, l'utilisateur doit s'inscrire et se connecter. Il pourra ainsi accéder à de nouvelles fonctionnalités :
* modifier les données d'une notice ;
* supprimer une notice ;
* ajouter une notice. 

Toutes ces modifications sont référencées : l'utilisateur connecté peut également avoir accès à une page listant des modifications effectuées.🖋


## Installation

Pour utliser cette application, vous devez être sous Linux et utliser Python3. Vous devez cloner le dépôt github, y créer un environnement virtuel, installer les librairies utilisées et, enfin, lancer l'application.

Installer l'application :
* Cloner le dépôt Devoir_Python_2021 : `git clone https://github.com/Marie-TNAH/Devoir_Python_2021`;
* Aller dans le dossier Devoir_Python_2021 : `cd Devoir_Python_2021`;
* Créer l'environnement virtuel : `virtualenv env -p python3` ;
* Installer les librairies :
  * installer le framework Flask : `pip install Flask`;
  * installer l'extension Flask-SQLAlchemy : `pip install flask_sqlalchemy`;
  * installer la library Flask-Login : `pip install flask-login` ;
* Lancer l'application :
  * activer l'environnement virtuel : `source env/bin/activate` ;
  * aller dans le répertoire Mis en registre : `cd Mis_en_registre` ;
  * aller dans le répertoire application `cd application` ;
  * lancer l'application : `python routes.py` ;
  * cliquer sur le lien fourni : http://127.0.0.1:5000/. 
 
 Bonne navigation !

