# Blank Social Skills — Claude Code

4 skills para social media baseadas na metodologia da agência Blank, prontas para usar no Claude Code.

## Skills incluídas

| Skill | O que faz |
|---|---|
| `social-posicionamento` | Diagnóstico e planejamento estratégico de posicionamento de marca |
| `social-curadoria` | Curadoria de conteúdo (passiva, ativa e via Apify), geração de pautas, operação de produção |
| `social-escrita` | Roteiros para Reels e copywriting para Carrosseis |
| `social-story` | Arquitetura de Stories — narrativa diária, funil de vendas, consistência de persona |

## Instalação

Copie as pastas das skills para `~/.claude/skills/`:

```bash
cp -r social-curadoria ~/.claude/skills/
cp -r social-escrita ~/.claude/skills/
cp -r social-posicionamento ~/.claude/skills/
cp -r social-story ~/.claude/skills/
```

## Uso

As skills disparam automaticamente no Claude Code quando o contexto é relevante. Também podem ser ativadas diretamente:

- `/social-posicionamento` — planejamento estratégico de marca
- `/social-curadoria` — curadoria e pautas (inclui busca ativa via Apify)
- `/social-escrita` — roteiros Reels / copy Carrosseis
- `/social-story` — estrutura e copy de Stories

## Curadoria Ativa (Apify)

A skill `social-curadoria` inclui um script para buscar posts reais do Instagram por hashtag ou perfil de concorrente, ordenados por engajamento.

Requer uma API Key gratuita do [Apify](https://apify.com) ($5/mês de créditos incluídos no plano free).

```bash
python social-curadoria/scripts/apify_curadoria.py \
  --api-key SUA_CHAVE \
  --hashtags "nutricionista,emagrecimento" \
  --nicho "nutrição funcional"
```

## Metodologia

Baseado nos cursos e frameworks da agência [Blank](https://agenciablank.com.br):
- Diagrama de Posicionamento (Você × Mercado × Sociedade)
- Matriz FBF (Fofoca Bem Feita)
- Curadoria 90/10 e Separação Tese × Tema
- Jogo do Volume vs Jogo do Alcance
- Funil de Narrativa para Vendas (Stories)
