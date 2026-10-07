document.addEventListener("DOMContentLoaded", async () => {
    // 1. INITIALISATION DE LA DB LOCALE (Mock data pour l'exemple)
    const mockData = await  getCustomerCatalogue() || [];

    // [
    //     { id_externe: "1020051", id_externe_marque: "1020051MON", nom_client: "AZOVSPECTECHNOLOGY LLC", code_dep: "NR", dc: "PEREZ GARCIA MATEO", dr: "PEREZ GARCIA MATEO", cust_sales_level_1: "1475 Export" },
    //     { id_externe: "1025551", id_externe_marque: "1025551MON", nom_client: "SAS Terres Cuites de Bourgogne", code_dep: "71", dc: "SIXT CLAUDE", dr: "QUINTANEIRO CARLOS", cust_sales_level_1: "2360 VENTES DIRECTES ENTREPRISES AUTRES" },
    //     { id_externe: "1029999", id_externe_marque: "1029999MON", nom_client: "Toiture de Lyon", code_dep: "69", dc: "SIXT CLAUDE", dr: "QUINTANEIRO CARLOS", cust_sales_level_1: "1475 Export" },
    //     { id_externe: "1031111", id_externe_marque: "1031111MON", nom_client: "Bati Sud", code_dep: "13", dc: "DURAND JEAN", dr: "MARTIN PAUL", cust_sales_level_1: "1100 GSS" }
    // ];

    // if (!Array.isArray(mockData)) {
    //     mockData = Object.values(mockData); 
    // }

    // Maintenant mockData est un tableau, le reste de votre code marchera !
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

    // 2. LOGIQUE D'AUTOCOMPLÉTION
    elements.search.addEventListener('input', function() {
        const val = this.value.toLowerCase();
        elements.autocompleteList.innerHTML = '';
        
        if (!val) {
            applyFilters();
            return;
        }

        const matches = clients.filter(c => 
            c.nom_client.toLowerCase().includes(val) || c.id_externe.includes(val)
        ).slice(0, 10); // Limite à 10 résultats pour ne pas surcharger

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
            const matchSearch = client.nom_client.toLowerCase().includes(searchVal) || client.id_externe.includes(searchVal);
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
    }

    // Attacher les événements aux filtres
    ['dr', 'dc', 'dep', 'h1','h2','h3'].forEach(key => {
        elements[key].addEventListener('change', applyFilters);
    });

    applyFilters(); // Initialisation au démarrage

    // 4. GESTION DU TERMINAL ET DU JOB
    const terminal = document.getElementById('terminal-sidebar');
    const terminalContent = document.getElementById('terminal-content');

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

    document.getElementById('btn-launch-job').addEventListener('click', () => {
        const clientCount = parseInt(elements.count.textContent);
        if (clientCount === 0) {
            alert("Veuillez sélectionner au moins un client pour générer une grille.");
            return;
        }

        // Préparation du payload
        const payload = {
            marque: document.getElementById('marque').value,
            type_grille: document.getElementById('type-grille').value,
            filters: {
                search: elements.search.value,
                dr: elements.dr.value,
                dc: elements.dc.value,
                dep: elements.dep.value,
                h1: elements.h1.value
            }
        };

        // Ouverture du terminal et simulation
        terminal.classList.add('open');
        terminalContent.innerHTML = ''; // Reset du terminal
        logToTerminal('Initialisation du worker...', 'info');
        logToTerminal(`Type: ${payload.type_grille.toUpperCase()} | Marque: ${payload.marque}`, 'warning');
        logToTerminal(`Extraction de ${clientCount} clients correspondants...`, 'info');

        // Simulation d'un appel réseau (à remplacer par ton vrai fetch)
        setTimeout(() => {
            logToTerminal('Connexion au serveur Flask établie.', 'success');
            logToTerminal('Génération des PDF/Excel en cours...', 'info');
            
            // ICI: METTRE TON VRAI FETCH VERS L'API FLASK
            /*
            fetch('/api/generer_grille', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(response => response.json()).then(data => {
                if(data.status === 'success') {
                    logToTerminal(data.message, 'success');
                } else {
                    logToTerminal(data.message, 'error');
                }
            }).catch(err => logToTerminal('Erreur de connexion : ' + err, 'error'));
            */

            // Simulation de la fin du job pour l'UX
            setTimeout(() => {
                logToTerminal('✔ Grille générée avec succès.', 'success');
                logToTerminal('Fichier enregistré dans : output/grilles/', 'info');
            }, 2000);

        }, 1000);
    });
});


async function getCustomerCatalogue() {
  const url = "http://127.0.0.1:5000/customer/catalogue"; 
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result)
    return result
  } catch (error) {
    console.error(error.message);
  }
}