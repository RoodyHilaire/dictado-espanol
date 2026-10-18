
import base64
import random
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# CONFIGURATION
# ============================================================

DOSSIER = Path(__file__).resolve().parent
DOSSIER_THEMES = DOSSIER / "themes"
DOSSIER_ASSETS = DOSSIER / "assets"

FICHIER_PHRASES_TEST = DOSSIER / "phrases.txt"
DOSSIER_AUDIO_TEST = DOSSIER / "audios"

SON_CORRECT = DOSSIER_ASSETS / "positive.wav"
SON_INCORRECT = DOSSIER_ASSETS / "negative.wav"

st.set_page_config(
    page_title="Mi Dictado — Dictée espagnole",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    /* Forcer une couleur lisible pour les textes principaux */
    .stApp,
    .stApp p,
    .stApp label,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stCaptionContainer"] {
        color: #243447;
    }

    /* Champs de saisie : texte sombre sur fond blanc */
    .stApp input,
    .stApp textarea,
    .stApp [data-baseweb="input"] input,
    .stApp [data-baseweb="textarea"] textarea {
        color: #243447 !important;
        background-color: #FFFFFF !important;
        -webkit-text-fill-color: #243447 !important;
        caret-color: #243447 !important;
    }

    /* Texte indicatif dans les champs */
    .stApp input::placeholder,
    .stApp textarea::placeholder {
        color: #7A8491 !important;
        -webkit-text-fill-color: #7A8491 !important;
        opacity: 1;
    }

    /* Fond des champs et bordures */
    .stApp [data-baseweb="input"] > div,
    .stApp [data-baseweb="textarea"] > div {
        background-color: #FFFFFF !important;
        border-color: #D6DBE2 !important;
    }

    /* Les boutons conservent leur propre style */
    .stApp button {
        color: inherit;
    }

    /* Texte des messages de validation */
    .stApp [data-testid="stAlert"] p {
        color: inherit;
    }

    
    .stApp {
        background-color: #F4F1E9;
    }

    [data-testid="stSidebar"] {
        background-color: #243447;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #AEBECD;
    }

    [data-testid="stSidebar"] button {
        width: 100%;
        min-height: 43px;
        text-align: left;
        border-radius: 8px;
        margin-bottom: 4px;
    }

    [data-testid="stSidebar"] button[kind="secondary"] {
        background: #30465D;
        border: 1px solid #30465D;
        color: white;
    }

    [data-testid="stSidebar"] button[kind="primary"] {
        background: #4C8C83;
        border: 1px solid #4C8C83;
        color: white;
    }

    .main .block-container {
        max-width: 1050px;
        padding: 2rem 3rem 2rem 3rem;
    }

    .titre-theme {
        color: #243447;
        font-size: 2rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .sous-titre {
        color: #596579;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .carte {
        background: white;
        border: 1px solid #DEDBD2;
        border-radius: 15px;
        padding: 28px;
        margin-top: 12px;
        margin-bottom: 18px;
    }

    .progression-label {
        color: #617086;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.04rem;
    }

    .score-label {
        color: #243447;
        font-size: 1rem;
        font-weight: 700;
        text-align: center;
        margin-top: 0.5rem;
    }

    .retour-correct {
        background: #E5F3EB;
        color: #247653;
        border-radius: 9px;
        padding: 14px 16px;
        font-weight: 700;
    }

    .retour-incorrect {
        background: #F8E8E3;
        color: #A34A35;
        border-radius: 9px;
        padding: 14px 16px;
        font-weight: 700;
    }

    .correction {
        color: #243447;
        font-size: 1.2rem;
        font-weight: 700;
        padding: 12px 0;
        overflow-wrap: anywhere;
    }

    div.stButton > button {
        border-radius: 9px;
        min-height: 43px;
        font-weight: 600;
    }

    div.stTextInput input {
        background: white;
        border-color: #D6DBE2;
        min-height: 48px;
        font-size: 1.05rem;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #DEDBD2;
        padding: 18px;
        border-radius: 12px;
    }

    @media (max-width: 800px) {
        .main .block-container {
            padding: 1.2rem 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FONCTIONS
# ============================================================

def normaliser(texte):
    """Reprend la normalisation de l'application Tkinter."""
    texte = texte.strip().casefold()

    guillemets = "\"'«»“”„"

    while (
        len(texte) >= 2
        and texte[0] in guillemets
        and texte[-1] in guillemets
    ):
        texte = texte[1:-1].strip()

    texte = re.sub(
        r"""[.!?¡¿…,"'«»“”„;:]+$""",
        "",
        texte,
    ).strip()

    return re.sub(r"\s+", " ", texte)


def charger_phrases(fichier):
    if not fichier.exists():
        return []

    with fichier.open("r", encoding="utf-8-sig") as f:
        return [
            ligne.strip()
            for ligne in f
            if ligne.strip()
        ]


def charger_themes():
    themes = {}

    # Thème de test facultatif à la racine.
    if FICHIER_PHRASES_TEST.exists():
        themes["Test général"] = {
            "phrases": FICHIER_PHRASES_TEST,
            "audios": DOSSIER_AUDIO_TEST,
        }

    # Détection automatique des chapitres.
    if DOSSIER_THEMES.exists():
        for dossier in sorted(DOSSIER_THEMES.iterdir()):
            if not dossier.is_dir():
                continue

            fichier_phrases = dossier / "phrases.txt"
            dossier_audio = dossier / "audios"

            if fichier_phrases.exists() and dossier_audio.exists():
                themes[dossier.name] = {
                    "phrases": fichier_phrases,
                    "audios": dossier_audio,
                }

    return themes


def lire_audio(chemin):
    if not chemin.exists():
        return None

    return chemin.read_bytes()


def jouer_son_resultat(chemin):
    """Joue le son de validation dans le navigateur."""
    donnees = lire_audio(chemin)

    if not donnees:
        return

    contenu = base64.b64encode(donnees).decode("ascii")

    html_audio = f"""
    <audio autoplay>
        <source src="data:audio/wav;base64,{contenu}"
                type="audio/wav">
    </audio>
    """

    components.html(
        html_audio,
        height=1,
        scrolling=False,
    )


def initialiser_theme(nom_theme, themes):
    configuration = themes[nom_theme]
    phrases = charger_phrases(configuration["phrases"])
    dossier_audio = configuration["audios"]

    if not phrases:
        st.session_state.erreur_theme = (
            f"Le chapitre « {nom_theme} » ne contient aucune phrase."
        )
        return False

    manquants = [
        f"phrase_{i:03d}.wav"
        for i in range(1, len(phrases) + 1)
        if not (dossier_audio / f"phrase_{i:03d}.wav").exists()
    ]

    if manquants:
        st.session_state.erreur_theme = (
            f"Le chapitre « {nom_theme} » possède des audios manquants : "
            + ", ".join(manquants[:8])
        )
        return False

    indices = list(range(len(phrases)))
    random.shuffle(indices)

    st.session_state.theme_actif = nom_theme
    st.session_state.phrases = phrases
    st.session_state.indices = indices
    st.session_state.position = 0
    st.session_state.score = 0
    st.session_state.repondu = False
    st.session_state.reponse = ""
    st.session_state.correcte = False
    st.session_state.termine = False
    st.session_state.historique = []
    st.session_state.erreur_theme = None

    # Déclenche la lecture automatique pour la nouvelle phrase.
    st.session_state.audio_autoplay_token = None

    return True


def choisir_theme(nom_theme):
    st.session_state.theme_demande = nom_theme


def passer_a_la_suivante():
    if st.session_state.position + 1 >= len(st.session_state.indices):
        st.session_state.termine = True
        st.session_state.audio_autoplay_token = None
        return

    st.session_state.position += 1
    st.session_state.repondu = False
    st.session_state.reponse = ""
    st.session_state.correcte = False
    st.session_state.audio_autoplay_token = None


def recommencer_theme():
    nom = st.session_state.theme_actif
    themes = st.session_state.themes_charges

    initialiser_theme(nom, themes)


def valider_reponse(reponse, phrase_attendue):
    reponse = reponse.strip()

    if not reponse:
        st.session_state.message_vide = True
        return

    st.session_state.message_vide = False
    correcte = normaliser(reponse) == normaliser(phrase_attendue)

    st.session_state.reponse = reponse
    st.session_state.correcte = correcte
    st.session_state.repondu = True

    if correcte:
        st.session_state.score += 1
        st.session_state.son_a_jouer = str(SON_CORRECT)
    else:
        st.session_state.son_a_jouer = str(SON_INCORRECT)

    st.session_state.historique.append({
        "numero": st.session_state.position + 1,
        "attendu": phrase_attendue,
        "reponse": reponse,
        "correcte": correcte,
    })


# ============================================================
# CHARGEMENT ET INITIALISATION
# ============================================================

themes = charger_themes()

if not themes:
    st.error(
        "Aucun chapitre trouvé. Chaque chapitre doit contenir "
        "un fichier phrases.txt et un dossier audios."
    )
    st.stop()

st.session_state.themes_charges = themes

valeurs_initiales = {
    "theme_actif": None,
    "theme_demande": None,
    "phrases": [],
    "indices": [],
    "position": 0,
    "score": 0,
    "repondu": False,
    "reponse": "",
    "correcte": False,
    "termine": False,
    "historique": [],
    "erreur_theme": None,
    "message_vide": False,
    "son_a_jouer": None,
    "audio_autoplay_token": None,
}

for cle, valeur in valeurs_initiales.items():
    if cle not in st.session_state:
        st.session_state[cle] = valeur

if st.session_state.theme_actif not in themes:
    premier_theme = next(iter(themes))
    initialiser_theme(premier_theme, themes)

if st.session_state.theme_demande:
    nom_demande = st.session_state.theme_demande
    st.session_state.theme_demande = None

    if nom_demande in themes and nom_demande != st.session_state.theme_actif:
        initialiser_theme(nom_demande, themes)

# Si un thème n'a pas pu être initialisé.
if not st.session_state.phrases:
    st.error(st.session_state.erreur_theme or "Impossible de charger ce chapitre.")
    st.stop()


# ============================================================
# MENU LATÉRAL
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 18px 4px 8px 4px;">
            <div style="font-size: 1.65rem; font-weight: 800;">
                🎧 MI DICTADO
            </div>
            <div style="color: #AEBECD; font-size: 0.8rem;
                        letter-spacing: 0.12rem; margin-top: 5px;">
                ENTRAÎNEMENT
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Choisir un thème")

    for nom_theme in themes:
        st.button(
            f"  {nom_theme}",
            key=f"theme_{nom_theme}",
            type=(
                "primary"
                if nom_theme == st.session_state.theme_actif
                else "secondary"
            ),
            use_container_width=True,
            on_click=choisir_theme,
            args=(nom_theme,),
        )

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.9rem; line-height: 1.5;">
            Sélectionne un thème pour commencer.<br>
            Les chapitres supplémentaires apparaîtront
            automatiquement dans ce menu.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SON DE VALIDATION EN ATTENTE
# ============================================================

if st.session_state.son_a_jouer:
    chemin_son = Path(st.session_state.son_a_jouer)
    st.session_state.son_a_jouer = None
    jouer_son_resultat(chemin_son)


# ============================================================
# EN-TÊTE PRINCIPAL
# ============================================================

nom_theme = st.session_state.theme_actif
phrases = st.session_state.phrases
indices = st.session_state.indices
position = st.session_state.position
total = len(indices)

st.markdown(
    f'<div class="titre-theme">{nom_theme}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sous-titre">Écoute, écris et progresse.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# ÉCRAN FINAL
# ============================================================

if st.session_state.termine:
    score = st.session_state.score
    pourcentage = round(score / total * 100) if total else 0

    st.markdown('<div class="carte">', unsafe_allow_html=True)

    st.markdown(
        "<h3 style='text-align:center; color:#4C8C83;'>"
        "THÈME TERMINÉ</h3>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h1 style='text-align:center; color:#243447;'>"
        "Bravo pour tes efforts !</h1>",
        unsafe_allow_html=True,
    )

    gauche, droite = st.columns(2)

    with gauche:
        st.metric("Score final", f"{score} / {total}")

    with droite:
        st.metric("Réussite", f"{pourcentage} %")

    st.progress(pourcentage)

    st.markdown(
        f"""
        <div style="text-align:center; color:#596579; line-height:1.9;">
            Thème : <b>{nom_theme}</b><br>
            Exercices terminés : <b>{total}</b><br>
            Réponses correctes : <b>{score}</b><br>
            Réponses incorrectes : <b>{total - score}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button(
        "↻ Recommencer ce thème",
        type="primary",
        use_container_width=True,
    ):
        recommencer_theme()
        st.rerun()

    with st.expander("Voir les corrections"):
        for element in st.session_state.historique:
            statut = "✓" if element["correcte"] else "✗"
            st.markdown(f"**{statut} Phrase {element['numero']}**")
            st.write(f"Phrase attendue : {element['attendu']}")
            st.write(f"Ta réponse : {element['reponse']}")
            st.divider()

    st.stop()


# ============================================================
# PROGRESSION
# ============================================================

st.markdown(
    f'<div class="progression-label">PHRASE {position + 1} SUR {total}</div>',
    unsafe_allow_html=True,
)

st.progress((position + 1) / total)

st.markdown('<div class="carte">', unsafe_allow_html=True)

st.markdown(
    "<h3 style='color:#243447; margin-top:0;'>"
    "Écris la phrase entendue :</h3>",
    unsafe_allow_html=True,
)

indice_phrase = indices[position]
phrase_attendue = phrases[indice_phrase]
chemin_audio = (
    themes[nom_theme]["audios"]
    / f"phrase_{indice_phrase + 1:03d}.wav"
)

# L'audio reste visible pour pouvoir le réécouter.
# Autoplay est demandé uniquement pour une nouvelle phrase.
token_audio = (nom_theme, position)
autoplay = st.session_state.audio_autoplay_token != token_audio

st.audio(
    chemin_audio.read_bytes(),
    format="audio/wav",
    autoplay=autoplay,
)

st.session_state.audio_autoplay_token = token_audio

st.caption("Écoute attentivement. Tu peux réécouter la phrase si nécessaire.")

if not st.session_state.repondu:
    with st.form(
        key=f"form_{nom_theme}_{position}",
        clear_on_submit=False,
    ):
        reponse = st.text_input(
            "Ta réponse en espagnol",
            key=f"reponse_{nom_theme}_{position}",
            placeholder="Écris ici ce que tu entends…",
        )

        valider = st.form_submit_button(
            "Vérifier ↵",
            type="primary",
            use_container_width=True,
        )

    if st.session_state.message_vide:
        st.warning("Écris d'abord ce que tu as entendu.")

    if valider:
        if not reponse.strip():
            st.session_state.message_vide = True
            st.rerun()
        else:
            valider_reponse(reponse, phrase_attendue)
            st.rerun()

else:
    if st.session_state.correcte:
        st.markdown(
            '<div class="retour-correct">✓ Correct !</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="retour-incorrect">'
            "Pas tout à fait. Voici la phrase attendue :"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="correction">{phrase_attendue}</div>',
            unsafe_allow_html=True,
        )

    st.caption(f"Ta réponse : {st.session_state.reponse}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Réécouter", use_container_width=True):
            # Le lecteur audio visible peut être relancé manuellement.
            st.info("Utilise le lecteur audio ci-dessus pour réécouter.")

    with col2:
        if st.button(
            "Phrase suivante →",
            type="primary",
            use_container_width=True,
        ):
            passer_a_la_suivante()
            st.session_state.message_vide = False
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f'<div class="score-label">'
    f'Score : {st.session_state.score} / {position + int(st.session_state.repondu)}'
    f'</div>',
    unsafe_allow_html=True,
)
