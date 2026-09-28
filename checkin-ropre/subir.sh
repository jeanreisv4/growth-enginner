#!/bin/zsh
# Publica o repositório em github.com/jeanreisv4/v4-checkin-ropre.
# Precisa de ~/.gh_token (fine-grained com Contents: read and write; Administration: write se o repo ainda não existir).
set -e
cd "$(dirname "$0")"
TOKEN=$(cat ~/.gh_token)
USER=jeanreisv4
REPO=v4-checkin-ropre
DESC="Skill do Claude Code que transforma os dados brutos do cliente em um check-in ROPRE — deck e documento — com a regra de atribuição declarada e o que não foi medido escrito na cara."

existe=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/$USER/$REPO)
if [ "$existe" != "200" ]; then
  echo "Repositório não existe; criando (precisa de Administration: write)..."
  curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
    https://api.github.com/user/repos -d "{\"name\":\"$REPO\",\"description\":\"$DESC\",\"private\":false,\"has_issues\":true,\"has_wiki\":false}" \
    | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('full_name') or d)"
fi

git remote remove origin 2>/dev/null || true
git remote add origin "https://$USER:$TOKEN@github.com/$USER/$REPO.git"
git push -u origin main
git remote set-url origin "https://github.com/$USER/$REPO.git"   # tira o token do remoto

curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$USER/$REPO -d "{\"description\":\"$DESC\"}" > /dev/null || true
curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$USER/$REPO/topics \
  -d '{"names":["claude-code","claude-skill","etl","marketing-analytics","client-reporting","python","mcp","growth"]}' > /dev/null || true
echo "pronto: https://github.com/$USER/$REPO"
