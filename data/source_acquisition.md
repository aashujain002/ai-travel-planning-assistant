# Singapore Source Acquisition

## 1. Wikivoyage Singapore Travel Guide

URL: https://en.wikivoyage.org/wiki/Singapore  
Status: accessible

### Useful sections
- **Districts:** Connects recommendations to areas such as Marina Bay, Chinatown, and Sentosa, enabling neighbourhood-specific questions and suggestions.
- **Understand:** Provides Singapore's cultural context, climate, and visitor expectations for practical travel advice.
- **Get around:** Covers tourist transport options and usage guidance without providing turn-by-turn navigation.
- **See:** Supplies notable sights and landmark details for attraction discovery and comparison.
- **Do:** Covers activities, including indoor and outdoor experiences, for interest-based recommendations.
- **Eat:** Provides hawker-centre culture, local dishes, and dining context for food-focused queries.
- **Stay safe:** Supports practical guidance on common safety and visitor considerations.

### Acquisition format
- `.html` to preserve the page's headings, linked district pages, and source structure for later processing.

### Notes
- Wikivoyage content is community maintained; time-sensitive facts should be verified against authoritative sources when answering users.
- The site publishes content under the Creative Commons Attribution-ShareAlike license, so reuse requires appropriate attribution and license compliance.

## 2. Visit Singapore – Plan Your Trip

URL: https://www.visitsingapore.com/mice/en/tools-and-resources/plan-your-trip/  
Status: accessible (redirects to the Singapore Destination Guide)

### Useful sections
- **Travel Tips:** Covers visa and entry requirements, drinking water, smoking rules, plugs, language, and weather, helping users prepare for a visit.
- **Money and Payment:** Explains Singapore dollar use, payment methods, tipping, and GST tax refunds, supporting practical spending guidance without processing payments.
- **Commuting around the island:** Introduces MRT, buses, LRT, taxis, and private-hire cars for general transport advice.
- **Public Transport:** Includes fare-payment options and accessibility information, helping visitors choose suitable ways to travel.
- **Curated for Your Downtime:** Provides itinerary pages for solo travellers, groups, and after-work activities, giving adaptable trip-planning patterns.
- **What's Happening in Singapore:** Links to current events and festivals, which can enrich time-specific activity suggestions when checked at response time.
- **Connectivity:** No dedicated connectivity or SIM-card section was found on the redirected page, so this source should not be relied on for connectivity guidance.

### Acquisition format
- `.html` to retain the guide's structured sections, cards, and links to its related itinerary and official-information pages.

### Notes
- The registry URL now redirects to an official Singapore Tourism Board MICE/business-leisure guide, so its content should be selected for relevance to general tourists.
- Visa rules, tax refunds, events, and transport details can change; link to or verify the current official information when responding.
- Review the Visit Singapore terms of use before storing or reusing page content.

## 3. Visit Singapore – Official Itineraries

URL: https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/  
Status: accessible

### Selected pages
- **4 Days in Singapore:** https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/4-days-in-singapore/
- **Enjoy Singapore in 7 Days:** https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/7-days-in-singapore/
- **Family Getaway in Singapore:** https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/places-to-visit-with-family/

### Useful sections
- **Introduction:** Provides the itinerary's purpose and traveller context.
- **Day sections:** Preserve multi-day sequencing for practical itinerary recommendations.
- **Activity tiles:** Supply attraction, food, culture, neighbourhood, and family-experience details.

### Acquisition format
- `.html` pages via HTTP.

### Notes
- The hub and individual pages use AEM structured component data rather than consistently rendered HTML headings.
- Four- and seven-day itineraries use `stb-things-to-do`; Family Getaway uses `stb-title-with-slider`. Both normalize into the same itinerary, section, and activity model.
- Review the Visit Singapore terms of use before storing or reusing page content.
