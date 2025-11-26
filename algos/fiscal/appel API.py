import requests
import pandas as pd
import io
import zipfile
"""
    Script qui récupère les declarations fiscales par arrondissement en utilisant une api parce que l appel api est 
    obligatoire dans le sujet. pas du tout pratique mais bon.
"""
dataset_id = "limpot-sur-le-revenu-par-collectivite-territoriale-ircom"
api_url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/"
annees_cibles = ["2020", "2021", "2022", "2023"]

print("Récupération des données fiscales Paris (2020-2023)...\n")

try:
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    dataset = response.json()
    resources = dataset.get('resources', [])
except requests.exceptions.RequestException as e:
    print(f"Erreur API: {e}")
    exit()

data_paris = []

for resource in resources:
    title = resource.get('title', '')
    url = resource.get('url', '')
    file_format = resource.get('format', '').lower()

    if not any(annee in title for annee in annees_cibles) or file_format != 'zip' or not url:
        continue

    print(f"Traitement: {title}")

    try:
        r_zip = requests.get(url, timeout=30)
        r_zip.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(r_zip.content)) as z:
            for filename in z.namelist():
                if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
                    continue

                try:
                    if filename.endswith('.xlsx'):
                        df = None
                        for header_row in range(0, 15):
                            try:
                                df_test = pd.read_excel(z.open(filename), header=header_row, dtype=str)
                                if 'Dép.' in df_test.columns:
                                    df = df_test
                                    break
                            except:
                                continue

                        if df is None:
                            continue
                    else:
                        df = pd.read_csv(z.open(filename), sep=';', dtype=str, encoding='latin-1', on_bad_lines='skip')

                    df.columns = df.columns.str.strip()

                    dep_col = None
                    for col in df.columns:
                        if col.lower().replace('.', '').strip() in ['dep', 'dép']:
                            dep_col = col
                            break

                    if dep_col is None:
                        continue

                    df[dep_col] = df[dep_col].astype(str).str.strip()

                    paris_rows = df[
                        (df[dep_col] == '75') |
                        (df[dep_col] == '075') |
                        (df[dep_col] == '750') |
                        (df[dep_col] == '754') |
                        (df[dep_col] == '755') |
                        (df[dep_col] == '756') |
                        (df[dep_col] == '757') |
                        (df[dep_col] == '758')
                        ].copy()

                    if not paris_rows.empty:
                        annee = None
                        for a in ['2020', '2021', '2022', '2023']:
                            if a in title:
                                annee = a
                                break

                        paris_rows['annee_declaration'] = annee
                        data_paris.append(paris_rows)
                        print(f"  {len(paris_rows)} lignes extraites")

                except Exception as e:
                    print(f"  Erreur: {e}")

    except Exception as e:
        print(f"  Erreur téléchargement: {e}")

print("\n" + "=" * 80)

if not data_paris:
    print("Aucune donnée trouvée pour Paris")
    exit()

df_final = pd.concat(data_paris, ignore_index=True)

colonnes_renommees = {
    'Dép.': 'departement',
    'Commune': 'code_commune',
    'Libellé de la commune': 'nom_commune',
    'Revenu fiscal de référence par tranche (en euros)': 'tranche_revenu',
    'Nombre de foyers fiscaux': 'nb_foyers_fiscaux',
    'Revenu fiscal de référence des foyers fiscaux': 'revenu_fiscal_reference',
    'Impôt net (total)*': 'impot_net_total',
    'Nombre de foyers fiscaux imposés': 'nb_foyers_imposes',
    'Revenu fiscal de référence des foyers fiscaux imposés': 'revenu_fiscal_imposes',
    'Traitements et salaires': 'traitements_salaires',
    'Retraites et pensions': 'retraites_pensions'
}

df_final = df_final.rename(columns=colonnes_renommees)

colonnes_finales = [
    'annee_declaration',
    'departement',
    'code_commune',
    'nom_commune',
    'tranche_revenu',
    'nb_foyers_fiscaux',
    'revenu_fiscal_reference',
    'impot_net_total',
    'nb_foyers_imposes',
    'revenu_fiscal_imposes',
    'traitements_salaires',
    'retraites_pensions'
]

colonnes_existantes = [col for col in colonnes_finales if col in df_final.columns]
df_final = df_final[colonnes_existantes]

df_final = df_final.drop_duplicates()
df_final = df_final.sort_values(['annee_declaration', 'code_commune', 'tranche_revenu'])

output_file = "donnees_paris_2020_2023.csv"
df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')

print(f"\nRésultat: {len(df_final)} lignes")
print(f"Années: {sorted(df_final['annee_declaration'].unique())}")
print(f"Fichier: {output_file}")
print(f"\nAperçu:\n{df_final.head(10)}")