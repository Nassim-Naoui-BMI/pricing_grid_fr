document.addEventListener("DOMContentLoaded", async () => {    
    
    
    // 1. INITIALISATION DE LA DB LOCALE (Mock data pour l'exemple)
    const mockData = await  getCustomerCatalogue() || [];

    localStorage.setItem("clientsDB", JSON.stringify(mockData));
    const clients = JSON.parse(localStorage.getItem("clientsDB"));
    console.log(clients)

    
    // Éléments du DOM
    const elements = {
        search: document.getElementById('search-client'),
        autocompleteList: document.getElementById('autocomplete-list'),
        dr: document.getElementById('filter-dr'),
        dc: document.getElementById('filter-dc'),
        dep: document.getElementById('filter-dep'),
        h1: document.getElementById('filter-h1'),
        h2: document.getElementById('filter-h2'),
        h3: document.getElementById('filter-h3'),
        tableBody: document.querySelector('#clients-table tbody'),
        count: document.getElementById('client-count')
    };

    let currentFilteredIds = []

    // 2. LOGIQUE D'AUTOCOMPLÉTION
    elements.search.addEventListener('input', function() {
        const val = this.value.toLowerCase();
        elements.autocompleteList.innerHTML = '';
        
        if (!val) {
            applyFilters();
            return;
        }

        const matches = clients.filter(c => {
            const nomClient = c.nom_client ? String(c.nom_client).toLowerCase() : "";
            const idExterne = c.id_externe ? String(c.id_externe).toLowerCase() : "";
            
            return nomClient.includes(val) || idExterne.includes(val);
        }).slice(0, 10);

        matches.forEach(match => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${match.id_externe}</strong> - ${match.nom_client}`;
            li.addEventListener('click', () => {
                elements.search.value = match.id_externe; // Rempli avec l'ID précis
                elements.autocompleteList.innerHTML = '';
                applyFilters(); // Déclenche le filtre général
            });
            elements.autocompleteList.appendChild(li);
        });
        
        applyFilters(); // Applique le filtre en cours de frappe
    });

    // Fermer l'autocomplétion si on clique en dehors
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-container')) {
            elements.autocompleteList.innerHTML = '';
        }
    });

    // 3. LOGIQUE DES FILTRES ET DU TABLEAU
    function getUniqueValues(data, key) {
        return [...new Set(data.map(item => item[key]))].filter(Boolean).sort();
    }

    function populateSelect(selectElement, options, currentValue) {
        selectElement.innerHTML = '<option value="">Toutes / Tous</option>';
        options.forEach(opt => {
            const optionEl = document.createElement('option');
            optionEl.value = opt;
            optionEl.textContent = opt;
            if (opt === currentValue) optionEl.selected = true;
            selectElement.appendChild(optionEl);
        });
    }

    function renderTable(data) {
        elements.tableBody.innerHTML = '';
        data.forEach(client => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${client.id_externe}</td>
                <td>${client.nom_client}</td>
                <td>${client.code_dep}</td>
                <td>${client.dc}</td>
            `;
            elements.tableBody.appendChild(tr);
        });
        elements.count.textContent = data.length;
    }

    function applyFilters() {
        const searchVal = elements.search.value.toLowerCase();
        const drVal = elements.dr.value;
        const dcVal = elements.dc.value;
        const depVal = elements.dep.value;
        const h1Val = elements.h1.value;
        const h2Val = elements.h2.value;
        const h3Val = elements.h3.value;

        const filteredClients = clients.filter(client => {
            const nomClient = client.nom_client ? String(client.nom_client).toLowerCase() : "";
            const idExterne = client.id_externe ? String(client.id_externe).toLowerCase() : "";
            const matchSearch = nomClient.includes(searchVal) || idExterne.includes(searchVal);
            const matchDr = drVal ? client.dr === drVal : true;
            const matchDc = dcVal ? client.dc === dcVal : true;
            const matchDep = depVal ? client.code_dep === depVal : true;
            const matchH1 = h1Val ? client.cust_sales_level_1 === h1Val : true;
            const matchH2 = h2Val ? client.cust_sales_level_2 === h2Val : true;
            const matchH3 = h3Val ? client.cust_sales_level_3 === h3Val : true;

            return matchSearch && matchDr && matchDc && matchDep && matchH1 && matchH2 && matchH3;
        });

        populateSelect(elements.dr, getUniqueValues(filteredClients, 'dr'), drVal);
        populateSelect(elements.dc, getUniqueValues(filteredClients, 'dc'), dcVal);
        populateSelect(elements.dep, getUniqueValues(filteredClients, 'code_dep'), depVal);
        populateSelect(elements.h1, getUniqueValues(filteredClients, 'cust_sales_level_1'), h1Val);
        populateSelect(elements.h2, getUniqueValues(filteredClients, 'cust_sales_level_2'), h2Val);
        populateSelect(elements.h3, getUniqueValues(filteredClients, 'cust_sales_level_3'), h3Val);

        renderTable(filteredClients); // Met à jour le tableau affiché

        currentFilteredIds = filteredClients.map(client => client.id_externe)
        
    }

    // Attacher les événements aux filtres
    ['dr', 'dc', 'dep', 'h1','h2','h3'].forEach(key => {
        elements[key].addEventListener('change', applyFilters);
    });

    applyFilters(); // Initialisation au démarrage

    // 4. GESTION DU TERMINAL ET DU JOB
    const terminal = document.getElementById('terminal-sidebar');
    const terminalContent = document.getElementById('terminal-content');
    const btnLaunchJob = document.getElementById('btn-launch-job');

    function logToTerminal(message, type = 'info') {
        const div = document.createElement('div');
        div.className = `log log-${type}`;
        const time = new Date().toLocaleTimeString();
        div.textContent = `[${time}] ${message}`;
        terminalContent.appendChild(div);
        terminalContent.scrollTop = terminalContent.scrollHeight; // Auto-scroll
    }

    document.getElementById('close-terminal').addEventListener('click', () => {
        terminal.classList.remove('open');
    });

    btnLaunchJob.addEventListener('click', () => {
        const clientCount = parseInt(elements.count.textContent);
        if (clientCount === 0) {
            alert("Veuillez sélectionner au moins un client pour générer une grille.");
            return;
        }

        // Préparation du payload avec le format JSON exact attendu
        const payload = {
            marque: document.getElementById('marque').value,
            type_grille: document.getElementById('type-grille').value,
            clients_ids: currentFilteredIds // Utilise le tableau d'IDs mis à jour par tes filtres
        };

        console.log(payload)

        // Ouverture du terminal et préparation de l'UI
        terminal.classList.add('open');
        terminalContent.innerHTML = ''; // Reset du terminal
        btnLaunchJob.disabled = true;   // Empêche le double clic pendant le traitement
        
        logToTerminal('Initialisation de la requête...', 'info');
        logToTerminal(`Génération pour ${clientCount} client(s) (Marque: ${payload.marque}, Type: ${payload.type_grille})...`, 'warning');

        try {
            // 1. Appel réseau POST vers la nouvelle route Flask
            fetch('/api/edit-grid', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(response => {
                if (!response.ok) {
                    logToTerminal(`Erreur serveur HTTP: ${response.status}`, 'error');
                }
            }).catch(err => {
                logToTerminal(`Erreur réseau: ${err.message}`, 'error');
            });

            // 2. Écoute immédiate des logs via la route SSE
            const evtSource = new EventSource("/api/progress");
            
            evtSource.onmessage = function(event) {
                const logData = JSON.parse(event.data);
                
                // Choix de la couleur selon l'étape du worker
                let logType = 'info';
                if (logData.step === 'START') logType = 'warning';
                if (logData.step === 'PROGRESS') logType = 'success';
                if (logData.step === 'DONE') logType = 'success';
                if (logData.step === 'ERROR') logType = 'error';

                // Écriture en temps réel dans le terminal
                logToTerminal(`[${logData.step}] ${logData.message}`, logType);
                
                // Si le job est terminé (succès ou échec), on ferme la connexion
                if (logData.step === "DONE" || logData.step === "ERROR") {
                    evtSource.close();
                    btnLaunchJob.disabled = false; // Réactivation du bouton
                }
            };

            evtSource.onerror = function(err) {
                console.error("Erreur de flux SSE:", err);
                logToTerminal("Erreur de connexion au flux de logs Redis.", "error");
                evtSource.close();
                btnLaunchJob.disabled = false;
            };

        } catch (error) {
            logToTerminal(`Erreur inattendue: ${error.message}`, 'error');
            btnLaunchJob.disabled = false;
        }
    });
});


async function getCustomerCatalogue() {
  const url = "/customer/catalogue"; 
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    return result
  } catch (error) {
    console.error(error.message);
  }
}