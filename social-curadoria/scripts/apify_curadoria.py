#!/usr/bin/env python3
"""
Curadoria Ativa via Apify — Social Curadoria (Blank Methodology)

Busca conteúdo real em alta no Instagram por hashtag ou perfil de concorrente,
e retorna estrutura pronta para geração de pautas com Tese × Tema.

Uso:
  python apify_curadoria.py --api-key SUA_CHAVE --hashtags "nutricionista,emagrecimento" --limite 15
  python apify_curadoria.py --api-key SUA_CHAVE --perfis "nutricionistax,nutricionistay" --limite 10
  python apify_curadoria.py --api-key SUA_CHAVE --hashtags "arquitetura" --perfis "studio_x" --nicho "arquitetura de interiores de alto padrão"
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("ERRO: pacote 'requests' não encontrado. Execute: pip install requests")
    sys.exit(1)

APIFY_BASE = "https://api.apify.com/v2"

# Actor IDs no Apify
ACTORS = {
    "instagram_hashtag": "apify~instagram-scraper",   # busca por hashtag
    "instagram_profile": "apify~instagram-scraper",   # busca por perfil
    "google_search":     "apify~google-search-scraper",  # fallback via Google
}


# ─────────────────────────────────────────────
# Apify API
# ─────────────────────────────────────────────

def run_actor_sync(actor_slug: str, input_data: dict, api_key: str, timeout: int = 120) -> list:
    """Executa um actor Apify de forma síncrona e retorna os itens do dataset."""
    url = f"{APIFY_BASE}/acts/{actor_slug}/run-sync-get-dataset-items"
    params = {"token": api_key, "timeout": timeout, "memory": 256}
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, params=params, headers=headers,
                             json=input_data, timeout=timeout + 10)
    except requests.exceptions.Timeout:
        print(f"  ⚠ Timeout ao executar {actor_slug} (>{timeout}s). Tente reduzir --limite.")
        return []
    except requests.exceptions.ConnectionError:
        print("  ⚠ Erro de conexão. Verifique sua internet.")
        return []

    if resp.status_code == 401:
        print("  ✗ API key inválida ou sem permissão. Verifique em apify.com/account/integrations")
        sys.exit(1)
    if resp.status_code == 402:
        print("  ✗ Limite de uso do plano gratuito atingido. Aguarde ou faça upgrade em apify.com")
        sys.exit(1)
    if not resp.ok:
        print(f"  ✗ Erro HTTP {resp.status_code}: {resp.text[:200]}")
        return []

    try:
        return resp.json()
    except json.JSONDecodeError:
        return []


def check_api_key(api_key: str) -> bool:
    """Valida a API key antes de executar."""
    url = f"{APIFY_BASE}/users/me"
    try:
        resp = requests.get(url, params={"token": api_key}, timeout=10)
        if resp.ok:
            data = resp.json().get("data", {})
            username = data.get("username", "usuário")
            plan = data.get("plan", {}).get("id", "free")
            print(f"  ✓ Conectado como @{username} (plano: {plan})")
            return True
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────
# Buscas específicas
# ─────────────────────────────────────────────

def buscar_por_hashtag(hashtag: str, api_key: str, limite: int = 15) -> list:
    """Busca posts recentes de uma hashtag no Instagram via Apify."""
    hashtag_clean = hashtag.strip().lstrip("#").replace(" ", "")
    url_hashtag = f"https://www.instagram.com/explore/tags/{hashtag_clean}/"

    print(f"  → Buscando #{hashtag_clean} no Instagram...")

    input_data = {
        "directUrls": [url_hashtag],
        "resultsType": "posts",
        "resultsLimit": limite,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }

    items = run_actor_sync(ACTORS["instagram_hashtag"], input_data, api_key, timeout=90)
    return items


def buscar_por_perfil(handle: str, api_key: str, limite: int = 12) -> list:
    """Busca posts recentes de um perfil público do Instagram."""
    handle_clean = handle.strip().lstrip("@")
    url_perfil = f"https://www.instagram.com/{handle_clean}/"

    print(f"  → Buscando perfil @{handle_clean} no Instagram...")

    input_data = {
        "directUrls": [url_perfil],
        "resultsType": "posts",
        "resultsLimit": limite,
        "proxy": {"useApifyProxy": True},
    }

    items = run_actor_sync(ACTORS["instagram_profile"], input_data, api_key, timeout=90)
    return items


def buscar_google_tendencias(nicho: str, api_key: str, limite: int = 10) -> list:
    """Busca tendências do nicho via Google como fallback ou complemento."""
    queries = [
        f"{nicho} tendências Instagram 2025",
        f"{nicho} conteúdo viral",
        f"site:instagram.com {nicho}",
    ]
    resultados = []

    for query in queries[:2]:  # limita para não estourar quota
        print(f"  → Buscando no Google: \"{query}\"...")
        input_data = {
            "queries": query,
            "resultsPerPage": limite // 2,
            "maxPagesPerQuery": 1,
            "languageCode": "pt-br",
            "countryCode": "br",
        }
        items = run_actor_sync(ACTORS["google_search"], input_data, api_key, timeout=60)
        resultados.extend(items)

    return resultados


# ─────────────────────────────────────────────
# Processamento e saída
# ─────────────────────────────────────────────

def processar_posts_instagram(posts: list, fonte: str) -> list:
    """Normaliza posts do Instagram em estrutura de curadoria."""
    resultado = []
    for post in posts:
        if not isinstance(post, dict):
            continue

        caption = post.get("caption", "") or post.get("text", "") or ""
        likes = post.get("likesCount", 0) or post.get("likes", 0) or 0
        comments = post.get("commentsCount", 0) or post.get("comments", 0) or 0
        url = post.get("url", "") or post.get("shortCode", "")
        if url and not url.startswith("http"):
            url = f"https://www.instagram.com/p/{url}/"

        # Ignora posts sem caption
        if len(caption) < 20:
            continue

        resultado.append({
            "fonte": fonte,
            "caption_preview": caption[:200].replace("\n", " "),
            "likes": likes,
            "comments": comments,
            "engajamento_total": likes + comments,
            "url": url,
            "tipo": "instagram_post",
        })

    # Ordena por engajamento
    resultado.sort(key=lambda x: x["engajamento_total"], reverse=True)
    return resultado


def processar_resultados_google(items: list) -> list:
    """Normaliza resultados do Google em estrutura de curadoria."""
    resultado = []
    for item in items:
        if not isinstance(item, dict):
            continue
        titulo = item.get("title", "")
        descricao = item.get("description", "") or item.get("snippet", "")
        url = item.get("url", "") or item.get("link", "")

        if not titulo:
            continue

        resultado.append({
            "fonte": "google_search",
            "titulo": titulo,
            "descricao": descricao[:200],
            "url": url,
            "tipo": "google_result",
        })

    return resultado


def formatar_saida(instagram_posts: list, google_items: list, nicho: str) -> dict:
    """Monta o output final estruturado para geração de pautas."""
    top_posts = instagram_posts[:10]
    top_google = google_items[:5]

    return {
        "nicho": nicho,
        "total_posts_instagram": len(instagram_posts),
        "total_google": len(google_items),
        "top_posts_instagram": top_posts,
        "tendencias_google": top_google,
        "resumo_para_pautas": {
            "instrucao": (
                "Use os dados abaixo para gerar pautas com Tese × Tema. "
                "Cada pauta deve ter: Tema (derivado do post/tendência), "
                "Tese (ângulo único do posicionamento da marca), "
                "Formato sugerido e Alavanca estratégica."
            ),
            "sinais_de_engajamento": [
                {
                    "preview": p["caption_preview"][:120],
                    "engajamento": p["engajamento_total"],
                    "url": p["url"],
                }
                for p in top_posts[:5]
            ],
            "tendencias_identificadas": [
                {
                    "titulo": g["titulo"],
                    "descricao": g["descricao"][:100],
                }
                for g in top_google[:3]
            ],
        },
    }


# ─────────────────────────────────────────────
# Ajuda para obter a API key
# ─────────────────────────────────────────────

INSTRUCOES_API_KEY = """
╔══════════════════════════════════════════════════════════════════╗
║           Como obter sua API Key do Apify (2 minutos)           ║
╚══════════════════════════════════════════════════════════════════╝

1. Acesse: https://apify.com  (crie conta gratuita se não tiver)

2. Após o login, clique no seu avatar (canto superior direito)
   → Selecione "Settings"

3. No menu lateral, clique em "Integrations"

4. Em "Personal API tokens", clique em "Create new token"
   → Dê um nome (ex: "Claude Code")
   → Clique em "Create"

5. Copie o token gerado (começa com "apify_api_...")

6. Cole aqui quando solicitado, ou defina como variável de ambiente:
   export APIFY_API_KEY="apify_api_..."   (Mac/Linux)
   $env:APIFY_API_KEY="apify_api_..."     (Windows PowerShell)

ℹ  O plano gratuito inclui $5/mês em créditos de uso.
   Uma busca de hashtag consome ~$0.02–0.10 dependendo do volume.
"""


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Curadoria ativa de conteúdo Instagram via Apify"
    )
    parser.add_argument("--api-key", help="Apify API Key (ou use env APIFY_API_KEY)")
    parser.add_argument("--hashtags", help="Hashtags separadas por vírgula (ex: 'nutricionista,emagrecimento')")
    parser.add_argument("--perfis", help="@handles de concorrentes separados por vírgula (ex: 'perfil_x,perfil_y')")
    parser.add_argument("--nicho", default="", help="Descrição do nicho para contexto (ex: 'nutrição funcional')")
    parser.add_argument("--limite", type=int, default=15, help="Nº de posts por fonte (padrão: 15)")
    parser.add_argument("--instrucoes", action="store_true", help="Mostra como obter a API key")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Formato de saída")

    args = parser.parse_args()

    # Modo de instrução
    if args.instrucoes:
        print(INSTRUCOES_API_KEY)
        sys.exit(0)

    # Resolve API key
    api_key = args.api_key or os.environ.get("APIFY_API_KEY", "")
    if not api_key:
        print("\n✗ API key não fornecida.\n")
        print(INSTRUCOES_API_KEY)
        sys.exit(1)

    if not (args.hashtags or args.perfis):
        print("✗ Informe pelo menos --hashtags ou --perfis para buscar.")
        print("  Exemplo: --hashtags 'nutricionista,emagrecimento'")
        sys.exit(1)

    print(f"\n── Curadoria Ativa — Apify ──")
    print(f"Nicho: {args.nicho or '(não especificado)'}\n")

    # Valida key
    print("Verificando API key...")
    if not check_api_key(api_key):
        print("✗ Não foi possível validar a API key.")
        print(INSTRUCOES_API_KEY)
        sys.exit(1)
    print()

    instagram_posts = []
    google_items = []

    # Busca por hashtags
    if args.hashtags:
        for tag in [h.strip() for h in args.hashtags.split(",") if h.strip()]:
            posts = buscar_por_hashtag(tag, api_key, limite=args.limite)
            instagram_posts.extend(processar_posts_instagram(posts, f"#{tag}"))

    # Busca por perfis
    if args.perfis:
        for perfil in [p.strip() for p in args.perfis.split(",") if p.strip()]:
            posts = buscar_por_perfil(perfil, api_key, limite=args.limite)
            instagram_posts.extend(processar_posts_instagram(posts, f"@{perfil}"))

    # Busca Google como complemento (se nicho informado)
    if args.nicho:
        google_items = buscar_google_tendencias(args.nicho, api_key, limite=10)
        google_items = processar_resultados_google(google_items)

    # Monta resultado
    resultado = formatar_saida(instagram_posts, google_items, args.nicho)

    print(f"\n── Resultado ──")
    print(f"Posts Instagram encontrados: {resultado['total_posts_instagram']}")
    print(f"Resultados Google: {resultado['total_google']}")
    print()

    if args.output == "json":
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        # Saída texto legível
        print("=== TOP POSTS (por engajamento) ===\n")
        for i, post in enumerate(resultado["top_posts_instagram"][:8], 1):
            print(f"{i}. [{post['fonte']}] {post['caption_preview'][:100]}...")
            print(f"   Engajamento: {post['engajamento_total']:,} | {post['url']}\n")

        if resultado["tendencias_google"]:
            print("\n=== TENDÊNCIAS GOOGLE ===\n")
            for item in resultado["tendencias_google"][:5]:
                print(f"• {item['titulo']}")
                print(f"  {item['descricao'][:100]}\n")


if __name__ == "__main__":
    main()
