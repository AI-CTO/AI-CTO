#!/bin/bash
set -e  # Lopettaa skriptin, jos jokin komento epäonnistuu

echo "Tarkistetaan, että OPENAI_API_KEY on asetettu..."
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ ERROR: OPENAI_API_KEY ei ole asetettu!"
    exit 1
fi

echo "Käynnistetään sovellus..."
export OPENAI_API_KEY=${OPENAI_API_KEY}  # Asetetaan ympäristömuuttuja
poetry run python app.py &
APP_PID=$!

echo "Odotetaan, että sovellus käynnistyy..."
while ! nc -z 127.0.0.1 5000; do
    sleep 0.1
done
echo "✅ Sovellus käynnissä!"

echo "Ajetaan Robot Framework -testit..."
poetry run robot tests/

echo "Pysäytetään sovellus..."
kill $APP_PID || echo "⚠️ Prosessi $APP_PID ei ollut käynnissä."

echo "✅ Testit suoritettu."