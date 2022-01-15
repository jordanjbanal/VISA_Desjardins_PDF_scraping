2022-01-15

# Transactions VISA Desjardins PDF -> CSV

Noé Aubin-Cadot

Contexte :

- Les transactions VISA Desjardins dans Accesd ne sont pas au format CSV mais au format PDF.

But du script :

- Extraire les transactions des relevés Visa Desjardins au format PDF vers un format CSV.

Pour avoir les données de transactions PDF :

1. Aller au sommaire AccesD
2. En haut à droite, cliquer sur le bouton rond "Relevés et documents"
3. Cliquer sur "Cartes de Crédit et cartes prépayées"
4. Sélectionner la carte de crédit et la période désirée.
5. Télécharger les relevés en PDF.
6. Mettre les relevés PDF dans le dossier "input_pdf".

La librarie de scraping PDF utilisée est tabula : `pip3 install tabula`.

Lors de l'exécution de la commande Python `tabula.read_pdf(file,pages="all")` plus bas dans le script,
il se peut qu'une erreur pop-up dise que Java JDK n'est pas installé.
Pour remédier à ce problème il faut télécharger l'installateur ".dmg" de Java JDK sur le site d'Oracle ici [https://www.oracle.com/java/technologies/downloads/#license-lightbox]().
Pour Mac avec CPU Intel il faut choisir *x64 DMG Installer*.
Pour Mac avec CPU M1 il faut choisir *Arm 64 DMG Installer*, mais je n'ai pas testé ce dernier.