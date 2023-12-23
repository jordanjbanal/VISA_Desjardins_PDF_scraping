"""
2022-01-15
Noé Aubin-Cadot

But :
- Extraire les transactions des relevés Visa Desjardins PDF vers un format CSV

Défis :
- Scraping de PDF, pas toujours évident.
- Format des tables qui change dans le temps (à partir du 2021-05 la colonne "Numéro de transaction" disparaît et la colonne "Bonidollars" apparaît).

Pour avoir les données de transactions PDF :
-> Aller au sommaire AccesD
-> En haut à droite, cliquer sur le bouton rond "Relevés et documents"
-> Cliquer sur "Cartes de Crédit et cartes prépayées"
-> Sélectionner la carte de crédit et la période désirée.
-> Télécharger les relevés en PDF.
-> Mettre les relevés PDF dans le dossier "input_pdf".

Librarie de scraping PDF utilisée :
	pip3 install tabula
Lors de l'exécution de la commande Python
	tabula.read_pdf(file,pages="all")
il se peut qu'une erreur dise que Java JDK n'est pas installé.
Il faut alors télécharger l'installateur ".dmg" sur le site d'Oracle ici :
	https://www.oracle.com/java/technologies/downloads/#license-lightbox
Pour Mac avec CPU Intel il faut choisir "x64 DMG Installer".
Pour Mac avec CPU M1 il faut choisir "Arm 64 DMG Installer", mais je ne l'ai pas testé.

"""

################################################################################
################################################################################
# Importer des librairies

import numpy as np
import pandas as pd
import glob
import tabula # librarie de scraping de tables dans un fichier PDF
from tabula.io import read_pdf
import re # pour trouver la date du relevé dans le PDF
import PyPDF2
import chardet

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 10)
pd.set_option('max_colwidth', 100)
pd.set_option('display.width', 1000)

################################################################################
################################################################################
# Diverses fonctions

def nettoyage_montant(x):
	if pd.isna(x):
		return np.nan
	x = x.replace(',','.')
	x = x.replace(' ','')
	if 'CR' in x:
		x = '-'+x[:-2]
	return x

def nettoyage_description(description,description2,lieu):
	text = ''
	if len(description)>0:
		text+=' '+description.strip()
	if len(description2)>0:
		text+=' '+description2.strip()
	if len(lieu)>0:
		text+=' '+lieu.strip()
	return text.strip()

def extract_credit_pdf():
	input_files = glob.glob('input_pdf/*.pdf')
	input_files.sort()
	for input_file in input_files:
		print(input_file)
		# Premièrement on cherche la date du relevé dans le pdf
		with open(input_file, 'rb') as file:
			# Create a PDF reader object using PdfFileReader
			pdf_reader = PyPDF2.PdfFileReader(file)

			# Get the first page
			first_page = pdf_reader.getPage(0)

			# Extract text from the first page
			text = first_page.extractText()

			# Use chardet to detect the encoding
			result = chardet.detect(text.encode('utf-8'))

			# Get the detected encoding
			encoding = result['encoding']

			# Print the encoding
			print(f"PDF Encoding: {encoding}")

			# Use this encoding information to read the PDF with tabula
			#tables = tabula.read_pdf(input_file, encoding=encoding)

			# Now you can work with the DataFrame (df) extracted from the PDF
			tables = tabula.read_pdf(input_file, pages = '1', area = (0, 0, 1000, 1000), columns = [0], pandas_options={'header': None}, stream=True)
			table  = tables[0]
			text  = ' '.join(list(table[1]))
			regex = 'DATE DU RELEVÉ Jour [0-9][0-9] Mois [0-9][0-9] Année [0-9][0-9][0-9][0-9]'
			match_object = re.search(regex,text)
			match_string = match_object[0]
			DD   = match_string.split(' ')[4]
			MM   = match_string.split(' ')[6]
			YYYY = match_string.split(' ')[8]
			YYYY_MM = YYYY+'-'+MM
			YYYY_MM_DD = YYYY_MM+'-'+DD
			print(YYYY_MM)
			# Ensuite on fait le scraping du PDF pour trouver les transactions
			tables = tabula.read_pdf(input_file,pages="all")
			tables_utiles = []
			for df in tables:
				columns = list(df.columns)
				if 'Transactions effectuées avec la carte de : ' in columns[0]:
					tables_utiles.append(df)
			n=len(tables_utiles)
			print('Nombre de tables utiles :',n)
			df_out = pd.DataFrame(columns=['Numéro de transaction','Date de transaction',"Date d'inscription",'Description','Montant'])
			i=1
			for df in tables_utiles:
				print('Table numéro :',str(i)+'/'+str(n))
				i+=1
				df = df.copy()
				# À partir du 2021-05 il n'y a plus de numéro de transaction mais il y a les boni points
				if pd.to_datetime(YYYY_MM)<pd.to_datetime('2021-05'):
					df.columns = ['Description','Description 2','Lieu','Montant']
				else:
					if df.shape[1]==4:
						df.columns = ['Description','Description 2','Bonidollars','Montant']
						df['Lieu'] = ''
						df = df[['Description','Description 2','Lieu','Montant']]
					elif df.shape[1]==3:
						df.columns = ['Description','Bonidollars','Montant']
						df['Description 2'] = ''
						df['Lieu'] = ''
						df = df[['Description','Description 2','Lieu','Montant']] # ici Description 2 peut contenir le lieu, mais ça marche pareil avec le reste du script plus bas
						print(df)
					else:
						print('Problème')
						continue
				df = df.loc[3:]
				df['Description']   = df['Description'].fillna('').astype(str)
				df['Description 2'] = df['Description 2'].fillna('').astype(str)
				df['Lieu']          = df['Lieu'].fillna('').astype(str)
				df['Description']   = df[['Description','Description 2','Lieu']].apply(lambda x:nettoyage_description(x[0],x[1],x[2]),axis=1)
				df['Montant'] = df['Montant'].apply(lambda x:nettoyage_montant(x)).astype(float)
				df = df[['Description','Montant']]
				df = df[df['Description']!='Total'] # on drop la ligne Total à la fin si elle est présente
				df = df[df['Description']!='TOTAL'] # on drop la ligne TOTAL à la fin si elle est présente
				df = df[df['Montant'].notna()]
				df = df[df['Description']!='']
				df['Date de transaction'] = df['Description'].apply(lambda x:YYYY+'-'+'-'.join(x.split(' ')[0:2][::-1]))
				df["Date d'inscription"] = df['Description'].apply(lambda x:YYYY+'-'+'-'.join(x.split(' ')[2:4][::-1]))
				print(df)
				if pd.to_datetime(YYYY_MM)<pd.to_datetime('2021-05'):
					df['Numéro de transaction'] = df['Description'].apply(lambda x:x.split(' ')[4])
					df['Description'] = df['Description'].apply(lambda x:' '.join(x.split(' ')[5:]).strip())
				else:
					df['Numéro de transaction'] = ''
					df['Description'] = df['Description'].apply(lambda x:' '.join(x.split(' ')[4:]).strip())					
				df.reset_index(inplace=True,drop=True)
				df = df[['Numéro de transaction','Date de transaction',"Date d'inscription",'Description','Montant']]
				df_out = pd.concat([df_out, df], ignore_index=True)
			df_out.reset_index(inplace=True,drop=True)
			if pd.to_datetime(YYYY_MM)>=pd.to_datetime('2021-05'):
				m = len(df_out)
				df_out['Numéro de transaction'] = [f'{n+1:03}' for n in range(len(df_out))]
			print('\nTable :\n',df_out,sep='')
			output_file = 'output_csv/'+YYYY_MM+'.csv'
			df_out.to_csv(output_file,index=False)

def extract_credit_txt():
	path = 'input_txt'
	folders = glob.glob(path+'/*.txt')
	folders.sort()
	for folder in folders:
		year = folder.split('/')[-1]
		files = glob.glob(folder+'/*')
		files.sort()
		for file in files:
			month = file[-8:-6]
			year_month=year+'-'+month
			print(year_month)
			print(file)
			txt = open(file,'r')
			start=0
			colonnes = ["Date de transaction",
						"Date d'inscription",
						"Description",
						"Montant"]
			df = pd.DataFrame(columns=colonnes)
			df.index.name = "Numéro de transaction"
			for line in txt:
				if line[:19]=="Date de transaction":
					start=1
					continue
				if start:
					if line[:7]=="Total :":
						start=0
						break
					#print(len(line))
					#print(line)
					date_de_transaction   = line[:11]
					date_dinscription     = line[13:24]
					numero_de_transaction = line[26:29]
					description           = line[32:72]
					montant               = line[73:]
					montant = montant.strip('\n').strip('\t')
					# On s'assure que la description est correcte
					if "AVANCE D'ARGENT-ACCESD" in description:
						description = "AVANCE D'ARGENT-ACCESD"
						montant = line[55:]
						montant = float(montant.replace(',','.'))
					elif "DOLLAR AMERICAIN" in montant:
						montant = montant.split("AMERICAIN")[-1]
						montant = montant.strip()
						montant = float(montant.replace(',','.'))
					elif montant[0:2]=='CR':
						montant = montant[2:]
						montant = float(montant.replace(',','.'))
					else:
						montant = montant.replace(' ','')
						montant = float(montant.replace(',','.'))
					# On s'occupe de date_de_transaction
					jour,mois,annee     = date_de_transaction.split(' ')
					date_de_transaction = annee+'-'+dictionnaire_mois[mois]+'-'+jour
					# On s'occupe de date_dinscription
					jour,mois,annee     = date_dinscription.split(' ')
					date_dinscription = annee+'-'+dictionnaire_mois[mois]+'-'+jour
					do_print_preview=0
					if do_print_preview:
						print(date_de_transaction)
						print(date_dinscription)
						print(numero_de_transaction)
						print(description)
						print(montant)
					# On exporte dans un dataframe
					df.loc[numero_de_transaction,"Date de transaction"] = date_de_transaction
					df.loc[numero_de_transaction,"Date d'inscription"]  = date_dinscription
					df.loc[numero_de_transaction,"Description"]         = description
					df.loc[numero_de_transaction,"Montant"]         = montant
			print(df)
			df.to_csv("output/"+year_month+".csv")

################################################################################
################################################################################
# Utilisation des fonctions

# Extractions des transactions dans les relevés au format PDF
do_extract_credit_pdf=1
if do_extract_credit_pdf:
	extract_credit_pdf()

# Bonus :
# Extraction des transactions dans les relevés au format HTML (i.e. ".TXT") (moins utile car les relevés HTML disparaissent d'Accesd après 3 mois alors que ceux PDF restent)
do_extract_credit_txt=0
if do_extract_credit_txt:
	extract_credit_txt()




















