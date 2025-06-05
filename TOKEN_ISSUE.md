# ❌ PROBLEEM GEVONDEN!

Je Personal Access Token heeft niet de juiste "scopes" (permissies).

## 🔧 OPLOSSING: 

1. **Ga naar https://my.homey.app**
2. **Settings → Advanced → API Keys** 
3. **DELETE je huidige API key**
4. **Create API Key** opnieuw
5. **Zorg dat je ALLE scopes selecteert:**
   - ✅ Read devices
   - ✅ Write devices  
   - ✅ Read flows
   - ✅ Write flows
   - ✅ Read system
   - ✅ Write system
   - ✅ (alle andere beschikbare scopes)

6. **Kopieer de nieuwe token en update je .env file**

## 🧪 TIJDELIJKE WORKAROUND:

Voor nu kun je de server testen in offline mode:

```bash
make run-offline
```

Dit gebruikt demo data zodat je kunt testen of alles werkt voordat je een nieuwe token aanmaakt.

## ✅ DEMO DATA BESCHIKBAAR:

De offline mode heeft demo devices:
- Woonkamer Lamp (light)
- Temperatuur Sensor (sensor)

En demo flows:
- Goedemorgen Routine
- Avond Routine

Perfect om mee te testen!
