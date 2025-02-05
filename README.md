# Good to know

Un petit script python pour trier les photos par date de prise de vue.
Il va créer un dossier par année et un sous-dossier par mois. Il va ensuite copier les photos dans les bons dossiers et les renommer avec la date de prise de vue (format : YYYYMMDD_HHMMSS).

## Mise en place

* Install latest stable version of Python here : https://www.python.org/downloads/ 
  (Don't forget to check "Add Python to PATH" during the installation)
* Install librairies nécessaires : 'pip install' : pillow, tqdm, pillow_heif, piexif

## Utilisation

Exécuter la commande suivante en remplaçant "path/to/pictures" par le chemin du dossier contenant les photos à trier :

```bash
python .\sortPictures.py "path/to/pictures"
```
