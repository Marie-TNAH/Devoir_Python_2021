#!/usr/bin/python
# -*- coding: UTF-8 -*-


# On importe les librairies utiles:
import datetime
from flask import Flask, render_template, request, redirect, flash
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy


app = Flask("Application")
# On configure la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../db.sqlite'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = "Il n'est pas nécessaire d'espérer pour entreprendre ni de réussir pour persévérer."
# On définit le nombre de documents présentés par page pour utiliser une pagination
ENREGISTREMENTS_PAR_PAGES = 5

# On initie l'extension
db = SQLAlchemy(app)
login = LoginManager(app)

# On définit nos classes
# La table authorship nous permet de suivre l'évolution du contenu de l'application
class Authorship(db.Model):
    __tablename__ = "authorship"
    authorship_id = db.Column(db.Integer, nullable=True, autoincrement=True, primary_key=True)
    authorship_enregistrement_id = db.Column(db.Integer, db.ForeignKey('enregistrement.enregistrement_id'))
    authorship_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    authorship_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    authorship_type = db.Column(db.Text)
    user = db.relationship("User", back_populates="authorships")
    enregistrement = db.relationship("Enregistrement", back_populates="authorships")


# On crée notre modèle Enregistrement soit l'ensemble des éléments se rapportant à un même acte enregistré par le parlement de Paris
class Enregistrement (db.Model): 
    enregistrement_id= db.Column(db.Integer, unique=True, nullable=False, primary_key=True, autoincrement=True)
    enregistrement_nature=db.Column(db.Text)
    enregistrement_regeste=db.Column(db.Text)
    enregistrement_datedoc=db.Column(db.Text)
    enregistrement_motif=db.Column(db.Text)
    enregistrement_date=db.Column(db.Text)
    enregistrement_mode=db.Column(db.Text)
    enregistrement_chcomptes=db.Column(db.Text, nullable=False)
    #La jointure est faite avec User grâce à Authorship
    authorships = db.relationship("Authorship", back_populates="enregistrement")


class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True, autoincrement=True)
    user_nom = db.Column(db.Text, nullable=False)
    user_login = db.Column(db.String(45), nullable=False, unique=True)
    user_email = db.Column(db.Text, nullable=False)
    user_password = db.Column(db.String(100), nullable=False)
    #La jointure est faite avec Enregistrement grâce à Authorship
    authorships = db.relationship("Authorship", back_populates="user")

    @staticmethod
    def identification(login, motdepasse):
        """ Identifie un utilisateur. 
        :param login: Login de l'utilisateur
        :param motdepasse: Mot de passe envoyé par l'utilisateur
        """

        # On vérifie d'abord que le login existe  
        utilisateur = User.query.filter(User.user_login == login).first()
        # puis on vérifie que le mot de passe saisi correspond au mot de passe enregistré associé au login.
        if User.query.filter(User.user_password == motdepasse).first():
            # Si les deux sont validés et leur association également, alors l'authentification est réussie.
            return utilisateur
        return None

    def get_id(self):
        """ Retourne l'id de l'objet actuellement utilisé
        :returns: ID de l'utilisateur
        """
        return self.user_id

@login.user_loader
def charger_utilisateur(login):
    return User.query.get(int(login))


@app.route("/")
def accueil():
    """Route permettant l'affichage de la page d'accueil contenu dans un template html."""

    # Le nombre de documents à découvrir est affiché sur la page d'accueil. 
    enregistrements = Enregistrement.query.all()
    return render_template("pages/accueil.html", enregistrements=enregistrements)


@app.route("/presentation")
def presentation():
    """Route permettant l'affichage de la page de présentation du contenu de l'application. 
    C'est une page de texte dans un template html."""

    return render_template("pages/presentation.html")


@app.route("/decouvrir")
def decouvrir():
    """Route permettant de découvrir peu à peu le contenu de l'application,
     à raison de cinq documents par page.
    """

    #L'ensemble des documents sont listés.
    enregistrements = Enregistrement.query.all()
    # La page 1 est la première affichée.
    page = request.args.get("page", 1)

    # Les pages sont numérotées et les numéros sont des entiers. Il peut y avoir une page seulement.
    if isinstance(page, str) and page.isdigit():
        page = int(page)
    else:
        page = 1

    # La page comportant cinq enregistrements est d'abord définie comme une liste vide.  
    enregistrements_page = []

    # Si l'application comporte des documents référencés,
    if enregistrements:
        #alors ils sont répartis par cinq sur une même page suivant l'ordre de leur identifiant.
        enregistrements_page = Enregistrement.query.order_by(Enregistrement.enregistrement_id).paginate(page, per_page=ENREGISTREMENTS_PAR_PAGES)
        # La présentation de la pagination est régie par un template html.
        return render_template("pages/decouvrir.html", enregistrements_page=enregistrements_page, enregistrements=enregistrements)



@app.route("/enregistrement/<int:enregistrement_id>")
def enregistrement(enregistrement_id):
    """Route permettant de s'appesantir sur un enregistrement en particulier.
    :param enregistrement_id : identifiant du document référencé, automatiquement généré par la base de donnée, 
    il permet de compléter le nom de la route.
    """

    unique_enregistrement = Enregistrement.query.get(enregistrement_id)

    return render_template("pages/enregistrement.html", enregistrement=unique_enregistrement)

@app.route("/recherche")
def recherche():
    """ Route permettant la recherche plein-texte dans les regestes des documents.
    """

    # On définit une variable pour les termes qui sont saisis par les utilisateurs, soit un ou des mots clefs.
    motclef = request.args.get("keyword", None)
    
    # On crée une liste vide de résultats pouvant rester vide 
    # s'il n'y a pas de correspondance trouvée entre les mots clefs saisis par l'utilisateur et le contenu des regestes.  
    resultats = []

    # Les mots clefs sont comparés aux mots des regestes, 
    # et s'il existe des correspondances, la liste des documents concernés est stockée dans la variable résultats.
    # La variable rappel fait état du lien logique entre la page de recherche et la page de résultats.
    if motclef:
        resultats = Enregistrement.query.filter(Enregistrement.enregistrement_regeste.like("%{}%".format(motclef)))
        rappel = "Vous avez fait une requête avec le terme '" + motclef + "'."

    else:
        rappel = "Vous avez fait une requête avec le terme '" + motclef + "'."

    return render_template("pages/recherche.html", resultats=resultats, rappel=rappel, keyword=motclef)

@app.route("/recherche_nature")
def recherche_nature():
    """ Route permettant de rechercher un document selon sa nature grâce à un menu déroulant.
    """

    # On définit une variable correspondant au choix de recherche de l'utilisateur.
    motclef = request.args.get("keyword", None)

    # Les correspondances trouvées sont stockées dans une liste résultats, qui au départ est vide. 
    resultats = []

    # On définit l'attribut qui va être comparé aux mots clefs :
    enregistrement_nature = request.args.get("enregistrement_nature", None)

    # si des correspondances sont trouvées, la liste des documents en question est stockée dans la variable résultats.
    if enregistrement_nature:
        resultats = Enregistrement.query.filter(Enregistrement.enregistrement_nature == enregistrement_nature).all()

    return render_template("pages/recherche_nature.html", resultats=resultats, keyword=motclef)


@app.route("/recherche_avancee")
def recherche_avancee():
    """Route permettant de faire une recherche plein-texte parmi toutes les données de la base.
    La recherche est élargie au maximum.
    """

    # La variable motclef permet de stocker les termes saisis par l'utilisateur afin de les comparer 
    # à tous ceux renseignant les enregistrements.
    motclef = request.args.get("keyword", None)

    # On définit autant de listes vides que d'attributs renseignant un enregistrement.
    # L'objectif est de trier les résultats et d'indiquer à l'utilisateur à quel niveau de description
    # la correspondance a été trouvée (nature, regeste, dates, objet, mode d'enregistrement). 
    resultats1 = []
    resultats2 = []
    resultats3 = []
    resultats4 = []
    resultats5 = []
    resultats6 = []
    resultats7 = []

    # Liste des résultats générée si la correspondance est trouvée au niveau de la nature : 
    if motclef:
        resultats1=Enregistrement.query.filter(Enregistrement.enregistrement_nature.like("%{}%".format(motclef))).all()

    # Liste des résultats générée si la correspondance est trouvée au niveau du regeste :        
    if motclef:
        resultats2=Enregistrement.query.filter(Enregistrement.enregistrement_regeste.like("%{}%".format(motclef))).all()
    
    # Liste des résultats générée si la correspondance est trouvée au niveau de la date du document :     
    if motclef:
        resultats3=Enregistrement.query.filter(Enregistrement.enregistrement_datedoc.like("%{}%".format(motclef))).all()
    
    # Liste des résultats générée si la correspondance est trouvée au niveau de l'objet du document :     
    if motclef:
        resultats4=Enregistrement.query.filter(Enregistrement.enregistrement_motif.like("%{}%".format(motclef))).all()
    
    # Liste des résultats générée si la correspondance est trouvée au niveau de la date d'enregistrement :     
    if motclef:
        resultats5=Enregistrement.query.filter(Enregistrement.enregistrement_date.like("%{}%".format(motclef))).all()
    
    # Liste des résultats générée si la correspondance est trouvée au niveau du mode d'enregistrement :     
    if motclef:
        resultats6=Enregistrement.query.filter(Enregistrement.enregistrement_mode.like("%{}%".format(motclef))).all()
    
    # Liste des résultats générée si la correspondance est trouvée au niveau de la date d'enregistrement à la chambre des comptes :     
    if motclef:
        resultats7=Enregistrement.query.filter(Enregistrement.enregistrement_chcomptes.like("%{}%".format(motclef))).all()


    return render_template("pages/recherche_avancee.html", resultats1=resultats1, resultats2=resultats2, 
        resultats3=resultats3, resultats4=resultats4, resultats5=resultats5, resultats6=resultats6, resultats7=resultats7, 
        keyword=motclef)


@app.route("/index")
def index():
    """Route permettant d'accéder à l'ensemble des index.
    C'est une page de texte constituée de listes dans un template html."""

    return render_template("pages/index.html")


@app.route("/index_id")
def index_id():
    """Route permettant d'accéder à la liste des documents référencés selon l'ordre des identifiants."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_id).all()

    return render_template("pages/index_id.html", enregistrements=enregistrements)


@app.route("/index_nature")
def index_nature():
    """Route permettant d'accéder à la liste des documents référencés regroupés selon leur nature."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_nature).all()

    return render_template("pages/index_nature.html", enregistrements=enregistrements)


@app.route("/index_datedoc")
def index_datedoc():
    """Route permettant d'accéder à la liste des documents référencés regroupés selon leur date."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_datedoc).all()

    return render_template("pages/index_datedoc.html", enregistrements=enregistrements)


@app.route("/index_motif")
def index_motif():
    """Route permettant d'accéder à la liste des documents référencés regroupés selon leur motif."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_motif).all()

    return render_template("pages/index_motif.html", enregistrements=enregistrements)


@app.route("/index_date")
def index_date():
    """Route permettant d'accéder à la liste des documents référencés regroupés selon leur date d'enregistrement."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_date).all()

    return render_template("pages/index_date.html", enregistrements=enregistrements)

@app.route("/index_mode")
def index_mode():
    """Route permettant d'accéder à la liste des documents référencés regroupés selon leur mode d'enregistrement."""

    enregistrements = Enregistrement.query.order_by(Enregistrement.enregistrement_mode).all()

    return render_template("pages/index_mode.html", enregistrements=enregistrements)


@app.route("/index_chcomptes")
def index_chcomptes():
    """Route permettant d'accéder à la liste des documents ayant également fait l'objet d'un enregistrement à la Chambre des comptes."""

    # Les documents qui ont été enregistrés à la chambre des comptes n'ont pas la valeur 0.
    enregistrements = Enregistrement.query.filter(Enregistrement.enregistrement_chcomptes != "0").all()

    return render_template("pages/index_chcomptes.html", enregistrements=enregistrements)


@app.route("/non_chcomptes")
def non_chcomptes():
    """Route permettant d'accéder à la liste des documents n'ayant pas fait
    l'objet d'un enregistrement à la Chambre des comptes."""

    # Les documents qui n'ont pas été enregistrés à la chambre des comptes ont la valeur 0.
    enregistrements=Enregistrement.query.filter(Enregistrement.enregistrement_chcomptes=="0").all()

    return render_template("pages/non_chcomptes.html", enregistrements=enregistrements)


@login_required
@app.route("/ajout_document", methods=["POST","GET"])
def ajout_document():
    """Route accessible uniquement aux utilisateurs identifiés. 
    Elle permet d'ajouter les références d'un document enregistré par le parlement de Paris"""

    #L'ajout d'un nouvel enregistrement référencé se fait en méthode POST.
    if request.method== "POST":
        nature=request.form.get("nature", None)
        regeste=request.form.get("regeste", None)
        datedoc=request.form.get("datedoc", None)
        motif=request.form.get("motif", None)
        date=request.form.get("date", None)
        mode=request.form.get("mode", None)
        chcomptes=request.form.get("chcomptes", 0)

        # L'ajout n'est pas valide si le regeste ou la date d'enregistrement sont vides. 
        # Un message flash est alors envoyé à l'utilisateur pour signaler l'échec de l'enregistrement des données saisies.
        # Il est redirigé vers le formulaire pour pallier le ou les manques.
        if not regeste:
            flash("L'enregistrement des données saisies n'a pu aboutir : les champs regeste et date d'enregistrement sont obligatoires. N'oubliez pas de les remplir lors de votre prochaine tentative.")
            return redirect ("/ajout_document")

        if not date:
            flash("L'enregistrement des données saisies n'a pu aboutir : les champs regeste et date d'enregistrement sont obligatoires. N'oubliez pas de les remplir lors de votre prochaine tentative.")
            return redirect ("/ajout_document")  

        # Si les deux champs obligatoires sont renseignés, l'ajout est validé,
        # et ajouté dans la base de données.    
        if regeste and date:
            nv_doc=Enregistrement(
                enregistrement_nature=nature,
                enregistrement_regeste=regeste,
                enregistrement_datedoc=datedoc,
                enregistrement_motif=motif,
                enregistrement_date=date,
                enregistrement_mode=mode,
                enregistrement_chcomptes=chcomptes
                )
            db.session.add(nv_doc)
            db.session.commit()

            # Le message de validation récapitule les données enregistrées. 
            validation = "Vous avez enregistré les informations suivantes: {} | {} | {} | {} | {} | {} | {}. ".format(nature, regeste, 
                datedoc, motif, date, mode, chcomptes)

            # L'ajout est renseigné dans la la classe Authorship avec les identifiants de l'utilisateur à l'origine de l'ajout
            # et du nouveau document référencé.
            if nv_doc:
                enregistrement = Enregistrement.query.order_by(Enregistrement.enregistrement_id.desc()).limit(1).first()
                # L'indentifiant de l'enregistrement est sauvegardé si jamais le document est par la suite supprimé.
                num_a_retenir = enregistrement.enregistrement_id
                # L'attribut authorship_type nous permets d'avoir une vue d'ensemble des opérations faites 
                authorship_type = "a ajouté un document sur la base (n°{} au moment de sa création).".format(num_a_retenir)
                user = User.query.get(current_user.user_id)
                # Ces informations sont enregistrés dans la table Authorship.
                a_ajoute = Authorship(user=user, enregistrement=enregistrement, authorship_type=authorship_type)
                db.session.add(a_ajoute)
                db.session.commit()

            # Le message de validation évoqué ci-dessus appraît dans un template informant l'utilisateur du bon déroulé
            # des opérations. 
            return render_template("pages/validation_ajout.html", validation=validation, enregistrement=enregistrement)

    return render_template("pages/ajout_document.html")


@login_required
@app.route("/enregistrement/<int:enregistrement_id>/modification", methods=["POST","GET"])
def modification(enregistrement_id):
    """Route accessible uniquement aux utilisateurs identifiés. 
    Elle permet de modifier les références d'un document enregistré par le parlement de Paris.
    :param enregistrement_id : identifiant du document référencé permettant de compléter le nom de la route"""

    enregistrement = Enregistrement.query.get(enregistrement_id)

    # On stocke l'identifiant de l'enregistrement dans une variable qui devient pertinente en cas de suppression de l'enregistrement
    # L'objectif est d'enrichir la table Authorship.
    num_a_retenir = enregistrement.enregistrement_id

    # Les modifications se font en méthode POST. 
    if request.method== "POST":
        nature=request.form.get("nature", None)
        regeste=request.form.get("regeste", None)
        datedoc=request.form.get("datedoc", None)
        motif=request.form.get("motif", None)
        date=request.form.get("date", None)
        mode=request.form.get("mode", None)
        chcomptes=request.form.get("chcomptes", 0)

        # Les champs obligatoires sont toujours les mêmes (le regeste et la date d'enregistrement ne peuvent être vides).
        # Des messages flash sont là pour le rappeler. 
        if not regeste:
            flash("Les données que vous avez pu saisir sont perdues : les champs regeste et date d'enregistrement sont obligatoires. N'oubliez pas de les remplir lors de votre prochaine tentative.")
            

        if not date:
            flash("Les données que vous avez pu saisir sont perdues : les champs regeste et date d'enregistrement sont obligatoires. N'oubliez pas de les remplir lors de votre prochaine tentative.")
                   
        # Si les deux champs obligatoires sont renseignés, alors les données saisies remplacent les précédentes. 
        if regeste and date:
            enregistrement.enregistrement_nature=nature
            enregistrement.enregistrement_regeste=regeste
            enregistrement.enregistrement_datedoc=datedoc
            enregistrement.enregistrement_motif=motif
            enregistrement.enregistrement_date=date
            enregistrement.enregistrement_mode=mode
            enregistrement.enregistrement_chcomptes=chcomptes
            
            # Les données sont enregistrées.    
            db.session.add(enregistrement)
            db.session.commit()
            
            # Un message de validation est préparé récapitulant les données envoyées à la base de données.
            validation = "Vous avez enregistré les informations suivantes: {} | {} | {} | {} | {} | {} | {}. ".format(nature, regeste, 
            datedoc, motif, date, mode, chcomptes)

            # Si l'enregistrement a eu lieu, alors une ligne doit s'ajouter à la table Authorship :
            if enregistrement:
                # le type de modification est précisé avec l'identifiant que porte le document au moment de la modification.
                # Il ne disparaîtra pas, même si le document est supprimé, contrairement au authorship_enregistrement_id
                # qui lui dépend de l'identifiant de l'enregistrement. 
                authorship_type = "a modifié des données du document n°{}".format(num_a_retenir)
                user = User.query.get(current_user.user_id)
                a_modifie = Authorship(user=user, enregistrement=enregistrement, authorship_type=authorship_type)
                # Les informations sont enregistrées dans la table Authorship :
                db.session.add(a_modifie)
                db.session.commit()

                # L'utilisateur peut alors lire un message de validation dans un template html. 
            return render_template("pages/validation_modification.html", validation=validation, 
                enregistrement_id=enregistrement_id, enregistrement=enregistrement)

    return render_template ("pages/modification.html", enregistrement=enregistrement)


@login_required
@app.route("/enregistrement/<int:enregistrement_id>/suppression")
def suppression(enregistrement_id):
    """Route accessible uniquement aux utilisateurs identifiés. 
    Elle permet de supprimer les références d'un document enregistré par le parlement de Paris.
    :param enregistrement_id : identifiant du document référencé permettant de compléter le nom de la route"""

    # On définit une liste vide destinée à stocker le numéro d'identifiant du document au moment de sa suppression.
    num_a_retenir=[]

    enregistrement = Enregistrement.query.get(enregistrement_id)

    # Le numéro d'identifiant est conservé.
    num_a_retenir = enregistrement.enregistrement_id  

    # On renseigne la nature de la modification et le numéro d'identifiant du document concerné au moment de sa suppression.
    authorship_type = "a supprimé le document n°{}".format(num_a_retenir)

    # Le numéro d'identifiant est associé à la suppression :
    # il est possible de connaître l'identité de l'utilisateur y ayant procédé
    user = User.query.get(current_user.user_id)

    #Les informations sont rentrées dans la table Authorship avant la suppression de l'enregistrement. 
    a_supprime = Authorship(user=user, enregistrement=enregistrement, authorship_type=authorship_type)
    db.session.add(a_supprime)
    db.session.commit() 

    db.session.delete(enregistrement)
    db.session.commit()

    # L'utilisateur a la confirmation de sa suppression avec un message affiché dans un template html.
    return render_template ("pages/suppression.html", enregistrement_id=enregistrement_id)


@login_required
@app.route("/enregistrement/<int:enregistrement_id>/suppression_demandee")
def suppression_demandee(enregistrement_id):
    """Route accessible uniquement aux utilisateurs identifiés. 
    Elle permet de confirmer la suppression d'un enregistrement référencé.
    :param enregistrement_id : identifiant du document référencé permettant de compléter le nom de la route"""

    enregistrement = Enregistrement.query.get(enregistrement_id)

    # L'utilisateur confirme sa volonté après lecture d'un message l'informant de la conséquence de ses actes dans un template html.
    return render_template ("pages/suppression_demandee.html", enregistrement=enregistrement, enregistrement_id=enregistrement_id)



@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    """Route permettant à l'utiisateur de s'inscrire."""

    # On utlise la méthode POST puisque le formulaire d'inscription contient des données confidentielles.
    if request.method == "POST":
        # Les données sont saisies par l'utilisateur ; le formulaire se compose de quatre champs. 
        login=request.form.get("login", None)
        nom=request.form.get("nom", None)
        email=request.form.get("email", None)
        motdepasse=request.form.get("motdepasse", None)

        #Tous ces champs sont obligatoires.
        # Si l'un d'eux n'est pas rempli, l'utilisateur est renvoyé au formulaire d'inscription 
        # et un message d'erreur apparaît. 
        if not login:
            flash("Des erreurs ont été rencontrées durant votre inscription. Veuillez réessayer. Tous les champs doivent être remplis.")
            return redirect ("/inscription")

        if not nom:
            flash("Des erreurs ont été rencontrées durant votre inscription. Veuillez réessayer. Tous les champs doivent être remplis.")
            return redirect ("/inscription")

        if not email:
            flash("Des erreurs ont été rencontrées durant votre inscription. Veuillez réessayer. Tous les champs doivent être remplis.")
            return redirect ("/inscription")

        if not motdepasse:
            flash("Des erreurs ont été rencontrées durant votre inscription. Veuillez réessayer. Tous les champs doivent être remplis.")
            return redirect ("/inscription")

        # Si tous les champs sont remplis, alors les informations sont enregistrées dans la table User.
        if motdepasse and email and nom and login:
            nv_user=User(
                user_login=login,
                user_nom=nom,
                user_email=email,
                user_password=motdepasse
                )
            db.session.add(nv_user)
            db.session.commit()
            # Un message de confirmation informe l'utilisateur que son inscription a été prise en compte.
            # Le message liste ses informations confidentielles.
            validation = "Notez bien vos informations personnelles, en particulier votre login et mot de passe qui vous seront demandés à chaque connexion: {} | {} | {} | {} . ".format(
                login, nom, email, motdepasse)

            return render_template ("pages/validation_inscription.html", validation=validation)
            
    
    return render_template ("pages/inscription.html")


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    """Route permettant à l'utiisateur de se connecter et d'accéder ainsi à de nouvelles fonctionnalités."""

    # Cette situation ne devrait pas se produire car le bouton de connexion n'est pas accessible.
    # Néanmoins, il n'apparaît que si l'utilisateur relance la page confirmant sa connexion.
    if current_user.is_authenticated is True:
        flash("Vous êtes déjà connecté(e)")
        return redirect ("/")

    # La méthode POST est utilisée du fait de la confidentialité des informations.
    if request.method == "POST":
        # On utilise la fonction d'indentification définie au-dessus vérifiant le login, puis le mot de passe associé..
        utilisateur = User.identification(
            login=request.form.get("login", None),
            motdepasse=request.form.get("motdepasse", None)
        )

        if utilisateur:
            login_user(utilisateur)
            return render_template ("pages/validation_connexion.html")

        else:
            flash("Votre connexion n'a pas pu aboutir. Vérifier les données saisies ou inscrivez-vous si ce n'est pas encore fait.")
    
    return render_template("pages/connexion.html")
login.login_view = 'connexion'



@app.route("/deconnexion")
def deconnexion():
    """Route permettant de se déconnecter."""

    #On utilise la fonction logout_user de flask-login.
    if current_user.is_authenticated is True:
        logout_user()
        return render_template ("pages/validation_deconnexion.html")

    # Nous mettons un message d'erreur, si jamais l'utilisateur relançait la page confirmant sa déconnexion.
    # Le bouton de déconnexion n'apparaît pas si l'on est pas connecté.
    else:
        flash("Vous n'étiez pas connecté(e).")
        return redirect ("/")


@login_required
@app.route("/fonctionnement")
def fonctionnement():
    """Route permettant d'avoir une vue d'ensemble des évolutions apportées à l'application."""

    # L'utilisateur ne peut y avoir accès que s'il est identifié
    if current_user.is_authenticated is True:
        # On utilise la table Authorship qui permet de renseigner la date, le numéro de la modification, 
        # le document et le type de modification apportée.
        authorships = Authorship.query.order_by(Authorship.authorship_id).all()
        # On utilise les clefs primaire de la table User et étrangère de la table Authorship pour 
        # récupérer le login de l'utilisateur à l'origine de la modification. 
        user = User.query.filter(User.user_id == Authorship.authorship_user_id).all()

        return render_template ("pages/fonctionnement.html", authorships=authorships, user=user)



# On exécute ce fichier pour lancer l'application. 
if __name__ == "__main__":
    app.run(debug=True)
