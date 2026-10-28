# Plan: advanced flows terug in mcp-homey

Doel: Claude kan via deze MCP **advanced flows aanmaken en aanpassen** op de Homey Pro (lokale API), zonder kapotte flows achter te laten.

## Bevindingen (28/10/2026), getest tegen de echte Homey

- **De lokale API antwoordde enkel via HTTP.** HTTPS faalde, en `.env` stond nog op een oud IP met `HOMEY_USE_HTTPS=true`. `HomeyAPIClient.connect()` schakelt bij elke verbindingsfout **stil over naar demo-modus**. Dan lijkt alles te werken, maar met nepdata. `.env` is aangepast.
- **Root cause van de "null"-flows:** de oude code postte `{"advancedflow": {...}}`. Homey antwoordt dan 200, maar **negeert de body** en maakt een lege flow aan (`name: null`, `enabled: true`, `cards: {}`). Die lege flows lieten de Homey-app crashen met `localeCompare`. De juiste body is het flow-object **zelf**, zowel bij `POST` als bij `PUT`.
- **Kaartformaat:**
  - de keys van `cards` zijn UUID's
  - `id` is de volledige kaart-id, bv. `homey:manager:logic:webhook` of `homey:device:<uuid>:off`
  - `ownerUri` is optioneel: oudere flows hebben het, nieuwe niet
  - de verbindingen tussen kaarten lopen via `outputSuccess` / `outputTrue` / `outputFalse` / `outputError`, met daarin UUID's van andere kaarten
  - `all`/`any` gebruiken `input: ["<uuid>::outputTrue", ...]`
  - de builtin kaarten: `start`, `delay` (`args.delay = {number: "5", multiplier: 1|60}`) en `note` (`value`, `color`)
- **Volledig JSON-schema:** dit staat in het input-schema van de officiële Homey-connector-tool `create_advanced_flow`. Het is te bekijken via ToolSearch in Claude, en is de beste referentie die er bestaat.
- **Geverifieerd:** een flow aanmaken (webhook → melding, uitgeschakeld), updaten, ophalen (`broken: false`, 2 kaarten) en verwijderen werkt lokaal. Er staan geen kapotte flows meer op de Homey.

## Testen zonder Claude te herstarten

| Script | Wat het test |
|---|---|
| `scripts/flowlab.py` | rechtstreeks de HTTP-API: `cards`, `flows`, `get`, `create`, `update`, `delete` |
| `scripts/mcp_call.py` | de echte MCP-tool-laag: start bij elke aanroep een **verse** server via stdio, met de nieuwste code |

Werkwijze: wijzig de code, draai `mcp_call.py <tool> '<json>'` en kijk naar het resultaat. Claude moet je pas herstarten als alles af is.

Dumps (in `.gitignore`, want ze bevatten persoonlijke device-id's):
- `ref/flowcards/{trigger,condition,action}.json`: compacte versie (id, titel, args, tokens). Volledige versie in `*.full.json`.
- `ref/advancedflows/*.json`: de 17 bestaande flows, als voorbeelden van de echte structuur.

## Fase 1: client-laag ✅ (28/10/2026)

1. In `client/flows.py`: `create_advanced_flow`, `update_advanced_flow` en `delete_advanced_flow`, met de body **zonder wrapper**. `base.py` verwijst er nu al naar.
2. Eén functie `_validate_advanced_flow(flow, catalog)` die controleert:
   - `name` is een niet-lege string
   - elke kaart-key is een UUID
   - `trigger`/`condition`/`action`: de `id` bestaat in de catalogus, en de verplichte args uit de catalogus zijn ingevuld
   - elke referentie in `output*` en `input` wijst naar een bestaande kaart
   - er is minstens één `trigger` of `start`
   - bij een fout: een `ValueError` met een duidelijke reden, zodat de LLM zichzelf kan corrigeren
3. De catalogus = de drie `flowcard*`-endpoints, gecachet met `cache_ttl`.
4. `update_advanced_flow`: GET → wijzigingen erin mergen → PUT met de volledige flow.

## Fase 2: tools ✅ (28/10/2026, live getest via mcp_call.py)

5. Toevoegen in `tools/flow/management.py`:
   - `create_advanced_flow(name, cards, enabled=false, folder?, dry_run=true)`
   - `update_advanced_flow(id, name?, enabled?, cards?, dry_run=true)`
   - `delete_advanced_flow(id, confirm_name)`: verwijdert alleen als de naam overeenkomt
6. `get_flow_cards` uitbreiden met een `search`-parameter op id/titel. Er zijn 3000+ kaarten, dus zonder filter verdrinkt de LLM.
7. Elke tool testen via `scripts/mcp_call.py`.

## Fase 3: tests en afwerking (8 ✅, 11 deels: CLAUDE.md-notitie)

8. Unit-tests voor `_validate_advanced_flow`, met een geldige flow en kapotte varianten.
9. Een integratietest achter `HOMEY_INTEGRATION=1`: aanmaken → ophalen → `broken == false` checken → verwijderen.
10. Stille fallback naar demo-modus: alleen nog als `DEMO_MODE=true` expliciet aanstaat. Anders moet `connect()` een fout geven. Dit is los werk, maar het heeft vandaag de echte oorzaak verborgen.
11. `CLAUDE.md` en `README` aanpassen: flows zijn niet meer read-only.

## Bewust niet gedaan

- Gewone (standard) flows aanmaken.
- Een auto-layout-algoritme voor x/y: een simpel raster per kolom is genoeg.
- Cloud-OAuth: de lokale API key volstaat.
- `fix_corrupt_flows.py` terughalen: de oorzaak (de wrapper) is gevonden.
