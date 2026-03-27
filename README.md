# 🚀 B2B Hyper-Personalization Pipeline (SulAmérica Odonto)

Este projeto é um ecossistema de automação de prospecção focado no setor de saúde e benefícios. Ele resolve o problema da "prospecção fria" genérica, utilizando **Hiper-Personalização Dinâmica** e **Automação de UI** para aumentar drasticamente as taxas de conversão no WhatsApp.

---

## 💡 O Problema e a Solução

**O Problema:** Abordagens de vendas genéricas (Spam) são ignoradas ou bloqueadas. Donos de clínicas de estética recebem dezenas de mensagens automáticas diariamente e possuem "filtro" para textos longos.

**A Solução:** Um pipeline técnico que transforma leads brutos (Google Maps) em uma experiência de venda única:
1.  **Extração & Limpeza:** Coleta de leads geolocalizados em bairros estratégicos de Belo Horizonte (Lourdes, Savassi, Santo Agostinho).
2.  **Landing Page Dinâmica:** Uma página de vendas (Tailwind CSS) que se adapta via `URL Params` para injetar o nome da empresa e o bairro do cliente em tempo real no DOM.
3.  **Prova Visual Automatizada:** O sistema utiliza **Selenium** para simular um iPhone 12, acessa a página personalizada e gera um screenshot real da proposta exclusiva para ser enviado via WhatsApp.
4.  **CRM de Fluxo:** Persistência em CSV para controle de funil (Pendente, Enviado, Interessado).

---

## 🛠️ Tecnologias e Arquitetura

* **Linguagem:** Python 3.11 (Foco em Automação e Data Scraping)
* **Automação de Browser:** Selenium WebDriver (Chrome Headless)
* **Manipulação de Dados:** Pandas (Engine para o micro-CRM local)
* **Frontend Sênior:** HTML5, Tailwind CSS (Design Mobile-First e Persuasivo)
* **Infraestrutura:** Git, Linux Debian, Ambiente Virtual (venv)

---

## 📂 Estrutura do Ecossistema

* `index.html`: Landing Page otimizada com injeção de dados via JavaScript.
* `automacao_total.py`: O "Orquestrador" que gerencia o ciclo: URL -> Screenshot -> CRM Update.
* `lead_scraper.py`: Inteligência de coleta e extração de dados brutos.
* `crm_vendas.py`: Script de persistência para gestão de contatos e status.

---

## ⚙️ Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/caiobaraujo/VendaOdonto.git](https://github.com/caiobaraujo/VendaOdonto.git)
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie o servidor local para a Landing Page:**
    ```bash
    python3 -m http.server 8000
    ```

5.  **Execute a esteira de produção:**
    ```bash
    python3 automacao_total.py
    ```

---

## 📈 Diferenciais Técnicos e de Negócio

* **Pattern Interrupt:** O uso de imagens personalizadas quebra o padrão de spam e gera curiosidade imediata.
* **Ancoragem de Preço:** Estratégia visual focada no baixo custo por vida (R$ 26,90) vs. alto valor de retenção de talentos.
* **Escalabilidade:** Arquitetura pronta para ser migrada para uma VPS ou integrada com orquestradores como **n8n**.
* **Segurança:** Arquivos sensíveis e dados de leads protegidos via `.gitignore`.

---

### 👨‍💻 Sobre o Desenvolvedor
**Caio Araújo** - Desenvolvedor Full-Stack focado em criar soluções que automatizam processos e geram ROI real para o negócio.
