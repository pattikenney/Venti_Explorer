"""
Venti Data Set Examples — Streamlit audio gallery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit_authenticator as stauth

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
AUDIO_ROOT = APP_DIR / "audio_library"
GALLERY_SETTINGS_PATH = AUDIO_ROOT / "gallery_settings.json"
GENERATED_DIR = AUDIO_ROOT / "generated"
CONDITIONING_CLIPS_DIR = AUDIO_ROOT / "conditioning_clips"

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"}

DEFAULT_SCRIPTED_STYLES = [
    "Default",
    "Confused",
    "Enunciated",
    "Happy",
    "Laughing",
    "Sad",
    "Whisper",
]

DEFAULT_UNSCRIPTED_STYLES = ["Default"]

# Valerie (gallery default label) — show first in Unscripted dialogue browse defaults.
UNSCRIPTED_PRIMARY_ACTOR = "actor_05"

SECTION_KEYS = [
    "scripted_sentences",
    "contrastive_emphasis",
    "numbers_emails",
    "long_form_material",
    "vad_personas",
    "singing",
    "generated_audio",
    "conditioning_clips",
    "unscripted_dialogue",
]

DEFAULT_SECTION_HELP: Dict[str, str] = {
    "scripted_sentences": (
        "A collection of scripted sentences. Pick an actor and style to browse clips."
    ),
    "contrastive_emphasis": "Contrastive emphasis recordings across actors and emphasis types.",
    "numbers_emails": "Numbers and email-style readings.",
    "long_form_material": "Longer passages: news vs. narrative.",
    "vad_personas": "Persona-conditioned deliveries.",
    "singing": "Singing category clips.",
    "generated_audio": (
        "Model-generated or synthetic clips. Files live under `audio_library/generated/`."
    ),
    "conditioning_clips": (
        "Reference / conditioning audio for models. Files live under "
        "`audio_library/conditioning_clips/`."
    ),
    "unscripted_dialogue": (
        "Spontaneous or conversational material. Uses **unscripted** styles (separate from "
        "scripted sentence styles). Path: `unscripted_dialogue/<actor>/<style>/`."
    ),
}


# ---------------------------------------------------------------------------
# Gallery settings
# ---------------------------------------------------------------------------


def _default_gallery_settings() -> Dict[str, Any]:
    return {
        "actor_labels": {f"actor_{i:02d}": f"Actor {i}" for i in range(1, 7)},
        "section_help": dict(DEFAULT_SECTION_HELP),
    }


def load_gallery_settings() -> Dict[str, Any]:
    if not GALLERY_SETTINGS_PATH.is_file():
        return _default_gallery_settings()
    try:
        data = json.loads(GALLERY_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _default_gallery_settings()
    base = _default_gallery_settings()
    if isinstance(data.get("actor_labels"), dict):
        base["actor_labels"].update(data["actor_labels"])
    if isinstance(data.get("section_help"), dict):
        base["section_help"].update(data["section_help"])
    for key in (
        "scripted_styles",
        "scripted_style_labels",
        "unscripted_styles",
        "unscripted_style_labels",
    ):
        if key in data:
            base[key] = data[key]
    return base


def save_gallery_settings(settings: Dict[str, Any]) -> None:
    GALLERY_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GALLERY_SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_actor_ids() -> List[str]:
    labels = load_gallery_settings().get("actor_labels") or {}
    if isinstance(labels, dict) and labels:
        return sorted(labels.keys())
    return [f"actor_{i:02d}" for i in range(1, 7)]


def format_actor_label(actor_id: str) -> str:
    labels = load_gallery_settings().get("actor_labels") or {}
    if isinstance(labels, dict) and actor_id in labels:
        return str(labels[actor_id])
    return actor_id


def load_scripted_styles() -> List[str]:
    raw = load_gallery_settings().get("scripted_styles")
    if isinstance(raw, list) and len(raw) > 0:
        return [str(x).strip() for x in raw if str(x).strip()]
    return list(DEFAULT_SCRIPTED_STYLES)


def format_style_label(folder_name: str) -> str:
    labels = load_gallery_settings().get("scripted_style_labels") or {}
    if isinstance(labels, dict) and folder_name in labels:
        return str(labels[folder_name])
    return folder_name.replace("_", " ").title()


def load_unscripted_styles() -> List[str]:
    raw = load_gallery_settings().get("unscripted_styles")
    if isinstance(raw, list) and len(raw) > 0:
        return [str(x).strip() for x in raw if str(x).strip()]
    return list(DEFAULT_UNSCRIPTED_STYLES)


def format_unscripted_style_label(folder_name: str) -> str:
    labels = load_gallery_settings().get("unscripted_style_labels") or {}
    if isinstance(labels, dict) and folder_name in labels:
        return str(labels[folder_name])
    return folder_name.replace("_", " ").title()


def load_section_help() -> Dict[str, str]:
    merged = dict(DEFAULT_SECTION_HELP)
    raw = load_gallery_settings().get("section_help") or {}
    if isinstance(raw, dict):
        merged.update({k: str(v) for k, v in raw.items()})
    return merged


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------


def list_audio_files(folder: Path) -> List[Path]:
    if not folder.is_dir():
        return []
    out: List[Path] = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS:
            out.append(p)
    return out


def count_audio_files(folder: Path) -> int:
    return len(list_audio_files(folder))


def coming_soon_message(folder: Path) -> None:
    if not folder.is_dir():
        st.warning(f"Folder not found on disk: `{folder}`")
        return
    if count_audio_files(folder) == 0:
        st.info("No audio files here yet — check back soon.")


def _audio_mime(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
    }.get(ext, "audio/wav")


def render_audio_list(files: List[Path]) -> None:
    if not files:
        return

    def _one_player(path: Path) -> None:
        try:
            data = path.read_bytes()
        except OSError:
            st.error(f"Could not read {path.name}")
            return
        st.audio(data, format=_audio_mime(path))

    if len(files) == 1:
        st.caption(files[0].name)
        _one_player(files[0])
        return

    ref = files[0]
    with st.container(border=True):
        st.markdown("**Reference clip**")
        st.caption(ref.name)
        _one_player(ref)

    st.divider()
    st.markdown("**Generated using the above clip as a conditioning clip**")
    for i, f in enumerate(files[1:], start=1):
        with st.container(border=True):
            st.markdown(f"**Generated output {i}**")
            st.caption(f.name)
            st.caption("Uses the reference clip above as conditioning.")
            _one_player(f)


def discover_ce_types() -> List[str]:
    actors = get_actor_ids()
    for aid in actors:
        base = AUDIO_ROOT / "contrastive_emphasis" / aid
        if base.is_dir():
            subs = sorted([d.name for d in base.iterdir() if d.is_dir()])
            if subs:
                return subs
    return [
        "agent",
        "baseline",
        "fact",
        "nature_of_fact",
        "relational",
        "temporal",
    ]


def discover_vad_personas() -> List[str]:
    actors = get_actor_ids()
    for aid in actors:
        base = AUDIO_ROOT / "vad_personas" / aid
        if base.is_dir():
            subs = sorted([d.name for d in base.iterdir() if d.is_dir()])
            if subs:
                return subs
    return ["best_friend", "motivator", "sage", "zen_monk"]


def humanize_label(s: str) -> str:
    return s.replace("_", " ").title()


def _pick_richest_actor(
    build_folder: Any,
) -> str:
    """Choose actor id with the most audio files under a path builder."""
    actors = get_actor_ids()
    best_a, best_n = actors[0], -1
    for a in actors:
        try:
            folder = build_folder(a)
        except Exception:
            continue
        n = count_audio_files(folder) if folder.is_dir() else 0
        if n > best_n:
            best_a, best_n = a, n
    return best_a


def _browse_default_scripted_pair() -> tuple[str, str]:
    styles = load_scripted_styles()
    if not styles:
        styles = list(DEFAULT_SCRIPTED_STYLES)
    actors = get_actor_ids()
    best_a, best_s = actors[0], styles[0]
    best_n = -1
    for a in actors:
        for s in styles:
            folder = AUDIO_ROOT / "scripted_sentences" / a / s
            n = count_audio_files(folder)
            if n > best_n:
                best_n, best_a, best_s = n, a, s
    return best_a, best_s


def _unscripted_actor_order() -> List[str]:
    ids = get_actor_ids()
    if UNSCRIPTED_PRIMARY_ACTOR in ids:
        return [UNSCRIPTED_PRIMARY_ACTOR] + [a for a in ids if a != UNSCRIPTED_PRIMARY_ACTOR]
    return ids


def _browse_default_unscripted_pair() -> tuple[str, str]:
    styles = load_unscripted_styles()
    if not styles:
        styles = list(DEFAULT_UNSCRIPTED_STYLES)
    actors = get_actor_ids()
    if UNSCRIPTED_PRIMARY_ACTOR in actors:
        best_n = -1
        best_s = styles[0]
        for s in styles:
            folder = AUDIO_ROOT / "unscripted_dialogue" / UNSCRIPTED_PRIMARY_ACTOR / s
            n = count_audio_files(folder)
            if n > best_n:
                best_n, best_s = n, s
        return UNSCRIPTED_PRIMARY_ACTOR, best_s
    best_a, best_s = actors[0], styles[0]
    best_n = -1
    for a in actors:
        for s in styles:
            folder = AUDIO_ROOT / "unscripted_dialogue" / a / s
            n = count_audio_files(folder)
            if n > best_n:
                best_n, best_a, best_s = n, a, s
    return best_a, best_s


# ---------------------------------------------------------------------------
# Browse sections
# ---------------------------------------------------------------------------


def section_scripted_sentences() -> None:
    st.info(load_section_help().get("scripted_sentences", DEFAULT_SECTION_HELP["scripted_sentences"]))
    if "browse_ss_actor" not in st.session_state:
        a, s = _browse_default_scripted_pair()
        st.session_state["browse_ss_actor"] = a
        st.session_state["ss_style"] = s
    styles = load_scripted_styles()
    if not styles:
        styles = list(DEFAULT_SCRIPTED_STYLES)
    if st.session_state.get("ss_style") not in styles:
        st.session_state["ss_style"] = styles[0]
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Actor",
            get_actor_ids(),
            format_func=format_actor_label,
            key="browse_ss_actor",
        )
    with c2:
        st.selectbox(
            "Style",
            styles,
            format_func=format_style_label,
            key="ss_style",
        )
    actor = st.session_state["browse_ss_actor"]
    style = st.session_state["ss_style"]
    folder = AUDIO_ROOT / "scripted_sentences" / actor / style
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_contrastive_emphasis() -> None:
    st.info(load_section_help().get("contrastive_emphasis", DEFAULT_SECTION_HELP["contrastive_emphasis"]))
    ce_types = discover_ce_types()
    if "browse_ce_actor" not in st.session_state:
        st.session_state["browse_ce_actor"] = _pick_richest_actor(
            lambda a: AUDIO_ROOT / "contrastive_emphasis" / a / ce_types[0]
        )
        st.session_state["ce_type"] = ce_types[0]
    if st.session_state.get("ce_type") not in ce_types:
        st.session_state["ce_type"] = ce_types[0]
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Actor",
            get_actor_ids(),
            format_func=format_actor_label,
            key="browse_ce_actor",
        )
    with c2:
        st.selectbox(
            "Emphasis type",
            ce_types,
            format_func=humanize_label,
            key="ce_type",
        )
    actor = st.session_state["browse_ce_actor"]
    et = st.session_state["ce_type"]
    folder = AUDIO_ROOT / "contrastive_emphasis" / actor / et
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_numbers_emails() -> None:
    st.info(load_section_help().get("numbers_emails", DEFAULT_SECTION_HELP["numbers_emails"]))
    if "browse_ne_actor" not in st.session_state:
        st.session_state["browse_ne_actor"] = _pick_richest_actor(
            lambda a: AUDIO_ROOT / "numbers_emails" / a
        )
    st.selectbox(
        "Actor",
        get_actor_ids(),
        format_func=format_actor_label,
        key="browse_ne_actor",
    )
    actor = st.session_state["browse_ne_actor"]
    folder = AUDIO_ROOT / "numbers_emails" / actor
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_long_form() -> None:
    st.info(load_section_help().get("long_form_material", DEFAULT_SECTION_HELP["long_form_material"]))
    modes = ["news_default", "book_narrative"]
    if "browse_lf_actor" not in st.session_state:
        st.session_state["browse_lf_actor"] = _pick_richest_actor(
            lambda a: AUDIO_ROOT / "long_form_material" / a / "news_default"
        )
        st.session_state["lf_mode"] = modes[0]
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Actor",
            get_actor_ids(),
            format_func=format_actor_label,
            key="browse_lf_actor",
        )
    with c2:
        st.selectbox(
            "Mode",
            modes,
            format_func=humanize_label,
            key="lf_mode",
        )
    actor = st.session_state["browse_lf_actor"]
    mode = st.session_state["lf_mode"]
    folder = AUDIO_ROOT / "long_form_material" / actor / mode
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_vad_personas() -> None:
    st.info(load_section_help().get("vad_personas", DEFAULT_SECTION_HELP["vad_personas"]))
    personas = discover_vad_personas()
    if "browse_vad_actor" not in st.session_state:
        st.session_state["browse_vad_actor"] = _pick_richest_actor(
            lambda a: AUDIO_ROOT / "vad_personas" / a / personas[0]
        )
        st.session_state["vad_persona"] = personas[0]
    if st.session_state.get("vad_persona") not in personas:
        st.session_state["vad_persona"] = personas[0]
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Actor",
            get_actor_ids(),
            format_func=format_actor_label,
            key="browse_vad_actor",
        )
    with c2:
        st.selectbox(
            "Persona",
            personas,
            format_func=humanize_label,
            key="vad_persona",
        )
    actor = st.session_state["browse_vad_actor"]
    persona = st.session_state["vad_persona"]
    folder = AUDIO_ROOT / "vad_personas" / actor / persona
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_singing() -> None:
    st.info(load_section_help().get("singing", DEFAULT_SECTION_HELP["singing"]))
    if "browse_sg_actor" not in st.session_state:
        st.session_state["browse_sg_actor"] = _pick_richest_actor(
            lambda a: AUDIO_ROOT / "singing" / a
        )
    st.selectbox(
        "Actor",
        get_actor_ids(),
        format_func=format_actor_label,
        key="browse_sg_actor",
    )
    actor = st.session_state["browse_sg_actor"]
    folder = AUDIO_ROOT / "singing" / actor
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def section_unscripted() -> None:
    st.info(load_section_help().get("unscripted_dialogue", DEFAULT_SECTION_HELP["unscripted_dialogue"]))
    if "browse_ud_actor" not in st.session_state:
        a, s = _browse_default_unscripted_pair()
        st.session_state["browse_ud_actor"] = a
        st.session_state["ud_style"] = s
    styles = load_unscripted_styles()
    if not styles:
        styles = list(DEFAULT_UNSCRIPTED_STYLES)
    if st.session_state.get("ud_style") not in styles:
        st.session_state["ud_style"] = styles[0]
    ud_order = _unscripted_actor_order()
    if st.session_state.get("browse_ud_actor") not in ud_order:
        st.session_state["browse_ud_actor"] = ud_order[0]
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Actor",
            ud_order,
            format_func=format_actor_label,
            key="browse_ud_actor",
        )
    with c2:
        st.selectbox(
            "Style (unscripted)",
            styles,
            format_func=format_unscripted_style_label,
            key="ud_style",
        )
    actor = st.session_state["browse_ud_actor"]
    style = st.session_state["ud_style"]
    folder = AUDIO_ROOT / "unscripted_dialogue" / actor / style
    coming_soon_message(folder)
    render_audio_list(list_audio_files(folder))


def page_browse() -> None:
    st.header("Browse")
    labels = [
        "Scripted sentences",
        "Contrastive emphasis",
        "Numbers & emails",
        "Long form material",
        "VAD personas",
        "Singing",
        "Unscripted dialogue",
    ]
    tab = st.tabs(labels)
    with tab[0]:
        section_scripted_sentences()
    with tab[1]:
        section_contrastive_emphasis()
    with tab[2]:
        section_numbers_emails()
    with tab[3]:
        section_long_form()
    with tab[4]:
        section_vad_personas()
    with tab[5]:
        section_singing()
    with tab[6]:
        section_unscripted()


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


def _admin_destination_folder(
    category: str,
    actor: str,
    extra: Optional[str] = None,
    extra2: Optional[str] = None,
) -> Path:
    if category == "scripted_sentences":
        style = extra or load_scripted_styles()[0]
        return AUDIO_ROOT / "scripted_sentences" / actor / style
    if category == "contrastive_emphasis":
        return AUDIO_ROOT / "contrastive_emphasis" / actor / (extra or discover_ce_types()[0])
    if category == "numbers_emails":
        return AUDIO_ROOT / "numbers_emails" / actor
    if category == "long_form_material":
        return AUDIO_ROOT / "long_form_material" / actor / (extra or "news_default")
    if category == "vad_personas":
        return AUDIO_ROOT / "vad_personas" / actor / (extra or discover_vad_personas()[0])
    if category == "singing":
        return AUDIO_ROOT / "singing" / actor
    if category == "unscripted_dialogue":
        style = extra or load_unscripted_styles()[0]
        return AUDIO_ROOT / "unscripted_dialogue" / actor / style
    if category == "generated":
        return GENERATED_DIR
    if category == "conditioning_clips":
        return CONDITIONING_CLIPS_DIR
    raise ValueError(f"Unknown category {category}")


def page_admin() -> None:
    st.header("Admin")
    tab_upload, tab_actor, tab_blurbs, tab_scripted, tab_unscripted = st.tabs(
        [
            "Upload audio",
            "Actor display names",
            "Section blurbs",
            "Scripted styles",
            "Unscripted styles",
        ]
    )
    with tab_upload:
        st.subheader("Upload audio")
        cats = [
            "scripted_sentences",
            "contrastive_emphasis",
            "numbers_emails",
            "long_form_material",
            "vad_personas",
            "singing",
            "unscripted_dialogue",
            "generated",
            "conditioning_clips",
        ]
        cat = st.selectbox("Category", cats, format_func=lambda c: c.replace("_", " ").title())
        actor: Optional[str] = st.selectbox(
            "Actor",
            get_actor_ids(),
            format_func=format_actor_label,
            disabled=(cat in ("generated", "conditioning_clips")),
        )
        extra = extra2 = None
        if cat == "scripted_sentences":
            styles = load_scripted_styles()
            extra = st.selectbox("Style folder", styles, format_func=format_style_label)
        elif cat == "contrastive_emphasis":
            extra = st.selectbox("Emphasis type", discover_ce_types(), format_func=humanize_label)
        elif cat == "long_form_material":
            extra = st.selectbox("Mode", ["news_default", "book_narrative"], format_func=humanize_label)
        elif cat == "vad_personas":
            extra = st.selectbox("Persona", discover_vad_personas(), format_func=humanize_label)
        elif cat == "unscripted_dialogue":
            ustyles = load_unscripted_styles()
            extra = st.selectbox(
                "Style folder (unscripted)",
                ustyles,
                format_func=format_unscripted_style_label,
            )
        dest = _admin_destination_folder(cat, actor, extra, extra2)
        st.caption(f"Destination: `{dest}`")
        up = st.file_uploader("Audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "aac"])
        if st.button("Save upload", type="primary") and up is not None:
            dest.mkdir(parents=True, exist_ok=True)
            name = Path(up.name).name
            target = dest / name
            target.write_bytes(up.getvalue())
            st.success(f"Saved to `{target}`")

    with tab_actor:
        st.subheader("Actor display names")
        settings = load_gallery_settings()
        labels = dict(settings.get("actor_labels") or {})
        for aid in get_actor_ids():
            labels[aid] = st.text_input(
                aid,
                value=str(labels.get(aid, aid)),
                key=f"actor_label_{aid}",
            )
        if st.button("Save actor labels", key="save_actor_labels"):
            settings["actor_labels"] = {aid: labels[aid].strip() or aid for aid in get_actor_ids()}
            save_gallery_settings(settings)
            st.success("Saved.")
            st.rerun()

    with tab_blurbs:
        st.subheader("Section blurbs")
        settings = load_gallery_settings()
        help_map = dict(settings.get("section_help") or {})
        for key in SECTION_KEYS:
            help_map[key] = st.text_area(
                key.replace("_", " ").title(),
                value=str(help_map.get(key, DEFAULT_SECTION_HELP.get(key, ""))),
                height=100,
                key=f"help_{key}",
            )
        if st.button("Save section blurbs", key="save_section_help"):
            settings["section_help"] = {k: help_map[k].strip() for k in SECTION_KEYS}
            save_gallery_settings(settings)
            st.success("Saved.")
            st.rerun()

    with tab_scripted:
        st.subheader("Scripted sentence style folders")
        st.caption(
            "Folder names must match directories under `scripted_sentences/<actor>/`. "
            "One folder name per line; same order for optional display labels."
        )
        settings = load_gallery_settings()
        styles_lines = "\n".join(load_scripted_styles())
        label_map = settings.get("scripted_style_labels") or {}
        ordered = load_scripted_styles()
        label_lines = "\n".join([str(label_map.get(s, "")) for s in ordered])
        t1 = st.text_area("Folder names (one per line)", value=styles_lines, height=160, key="admin_styles")
        t2 = st.text_area(
            "Display labels (one per line, optional)",
            value=label_lines,
            height=160,
            key="admin_style_labels",
        )
        if st.button("Save scripted styles", key="save_scripted_styles"):
            raw_lines = [ln.strip() for ln in t1.splitlines() if ln.strip()]
            if not raw_lines:
                st.error("Add at least one folder name.")
            elif any("/" in x or "\\" in x for x in raw_lines):
                st.error("Folder names cannot contain slashes.")
            else:
                lbl_lines = t2.splitlines()
                new_labels: Dict[str, str] = {}
                for i, folder in enumerate(raw_lines):
                    if i < len(lbl_lines) and lbl_lines[i].strip():
                        new_labels[folder] = lbl_lines[i].strip()
                settings["scripted_styles"] = raw_lines
                settings["scripted_style_labels"] = new_labels
                save_gallery_settings(settings)
                for k in list(st.session_state.keys()):
                    if k in ("ss_style", "browse_ss_actor") or k.startswith("admin_"):
                        try:
                            del st.session_state[k]
                        except KeyError:
                            pass
                st.success("Saved.")
                st.rerun()

    with tab_unscripted:
        st.subheader("Unscripted dialogue style folders")
        st.caption(
            "Folder names must match directories under `unscripted_dialogue/<actor>/`. "
            "Independent from scripted sentence styles. One folder per line; optional display labels."
        )
        settings = load_gallery_settings()
        styles_lines = "\n".join(load_unscripted_styles())
        label_map = settings.get("unscripted_style_labels") or {}
        ordered = load_unscripted_styles()
        label_lines = "\n".join([str(label_map.get(s, "")) for s in ordered])
        u1 = st.text_area(
            "Folder names (one per line)",
            value=styles_lines,
            height=160,
            key="admin_unscripted_styles",
        )
        u2 = st.text_area(
            "Display labels (one per line, optional)",
            value=label_lines,
            height=160,
            key="admin_unscripted_style_labels",
        )
        if st.button("Save unscripted styles", key="save_unscripted_styles"):
            raw_lines = [ln.strip() for ln in u1.splitlines() if ln.strip()]
            if not raw_lines:
                st.error("Add at least one folder name.")
            elif any("/" in x or "\\" in x for x in raw_lines):
                st.error("Folder names cannot contain slashes.")
            else:
                lbl_lines = u2.splitlines()
                new_labels: Dict[str, str] = {}
                for i, folder in enumerate(raw_lines):
                    if i < len(lbl_lines) and lbl_lines[i].strip():
                        new_labels[folder] = lbl_lines[i].strip()
                settings["unscripted_styles"] = raw_lines
                settings["unscripted_style_labels"] = new_labels
                save_gallery_settings(settings)
                for k in list(st.session_state.keys()):
                    if k in ("ud_style", "browse_ud_actor") or k.startswith("admin_unscripted"):
                        try:
                            del st.session_state[k]
                        except KeyError:
                            pass
                st.success("Saved.")
                st.rerun()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _secrets_section(name: str) -> Dict[str, Any]:
    if name not in st.secrets:
        return {}
    sec = st.secrets[name]
    if isinstance(sec, dict):
        return sec
    return {k: sec[k] for k in sec}


def build_authenticator() -> stauth.Authenticate:
    pw = _secrets_section("passwords")
    admin_pw = pw.get("admin", "admin")
    guest_pw = pw.get("guest", "guest")
    auth = _secrets_section("auth")
    cookie_name = str(auth.get("cookie_name", "research_audio_gallery"))
    cookie_key = str(auth.get("cookie_key", "replace-with-a-long-random-string-in-secrets"))
    cookie_expiry = float(auth.get("cookie_expiry_days", 7))
    credentials: Dict[str, Any] = {
        "usernames": {
            "admin": {
                "email": "admin@local",
                "name": "Admin",
                "password": str(admin_pw),
            },
            "guest": {
                "email": "guest@local",
                "name": "Guest",
                "password": str(guest_pw),
            },
        }
    }
    return stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry,
    )


def main() -> None:
    st.set_page_config(page_title="Venti Data Set Examples", layout="wide")
    authenticator = build_authenticator()
    authenticator.login()
    if st.session_state.get("authentication_status") is not True:
        if st.session_state.get("authentication_status") is False:
            st.error("Username or password is incorrect.")
        else:
            st.warning("Please sign in.")
        return

    with st.sidebar:
        st.caption(f"Signed in as **{st.session_state.get('name', '')}**")
        authenticator.logout(button_name="Log out", location="sidebar")
        st.divider()
        username = st.session_state.get("username", "")
        pages = ["Browse"]
        if username == "admin":
            pages.append("Admin")
        page = st.radio("Page", pages, label_visibility="collapsed")

    if page == "Browse":
        page_browse()
    else:
        page_admin()


if __name__ == "__main__":
    main()

