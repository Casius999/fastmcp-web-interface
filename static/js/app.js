document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const apiUrl = window.location.origin; // Base URL de l'API
    let tools = []; // Liste des outils disponibles
    let accessToken = localStorage.getItem('accessToken');
    
    // Éléments DOM
    const toolForm = document.getElementById('toolForm');
    const toolSelect = document.getElementById('tool');
    const paramFields = document.getElementById('paramFields');
    const toolDescription = document.getElementById('toolDescription');
    const resultContent = document.getElementById('resultContent');
    const loading = document.getElementById('loading');
    const loginForm = document.getElementById('loginForm');
    const loginSection = document.getElementById('loginSection');
    const toolSection = document.getElementById('toolSection');
    const userInfo = document.getElementById('userInfo');
    const userDisplayName = document.getElementById('userDisplayName');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginError = document.getElementById('loginError');
    
    // Vérifier si l'authentification est activée
    async function checkAuthRequired() {
        try {
            // Tenter d'appeler un endpoint qui ne nécessite pas d'authentification
            const response = await fetch(`${apiUrl}/health`);
            const data = await response.json();
            
            // Si l'endpoint /health est accessible, vérifier si l'utilisateur est connecté
            if (accessToken) {
                validateToken();
                return;
            }
            
            // Tenter d'appeler un endpoint protégé
            const testResponse = await fetch(`${apiUrl}/list_tools/`);
            
            // Si le statut est 401, l'authentification est requise
            if (testResponse.status === 401) {
                showLoginForm();
            } else {
                // Sinon, l'authentification n'est pas requise
                hideLoginForm();
                loadAvailableTools();
            }
        } catch (error) {
            console.error('Erreur lors de la vérification de l\'authentification:', error);
            // Par défaut, montrer l'interface d'outils
            hideLoginForm();
            loadAvailableTools();
        }
    }
    
    // Valider le token d'authentification
    async function validateToken() {
        try {
            const response = await fetch(`${apiUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                hideLoginForm();
                showUserInfo(userData.username);
                loadAvailableTools();
            } else {
                // Token invalide
                localStorage.removeItem('accessToken');
                accessToken = null;
                showLoginForm();
            }
        } catch (error) {
            console.error('Erreur lors de la validation du token:', error);
            localStorage.removeItem('accessToken');
            accessToken = null;
            showLoginForm();
        }
    }
    
    // Afficher le formulaire de connexion
    function showLoginForm() {
        loginSection.style.display = 'block';
        toolSection.style.display = 'none';
    }
    
    // Masquer le formulaire de connexion
    function hideLoginForm() {
        loginSection.style.display = 'none';
        toolSection.style.display = 'block';
    }
    
    // Afficher les informations de l'utilisateur
    function showUserInfo(username) {
        userDisplayName.textContent = username;
        userInfo.style.display = 'flex';
    }
    
    // Gérer la connexion
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        loginError.textContent = '';
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch(`${apiUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            
            if (response.ok) {
                const data = await response.json();
                accessToken = data.access_token;
                localStorage.setItem('accessToken', accessToken);
                hideLoginForm();
                showUserInfo(username);
                loadAvailableTools();
            } else {
                const error = await response.json();
                loginError.textContent = error.detail || 'Échec de la connexion';
            }
        } catch (error) {
            console.error('Erreur lors de la connexion:', error);
            loginError.textContent = 'Erreur de connexion au serveur';
        }
    });
    
    // Gérer la déconnexion
    logoutBtn.addEventListener('click', function() {
        localStorage.removeItem('accessToken');
        accessToken = null;
        showLoginForm();
        userInfo.style.display = 'none';
    });
    
    // Charger la liste des outils disponibles
    async function loadAvailableTools() {
        try {
            const headers = accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {};
            
            const response = await fetch(`${apiUrl}/list_tools/`, {
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('Échec de la récupération des outils');
            }
            
            const data = await response.json();
            tools = data.tools;
            
            // Vider le select
            toolSelect.innerHTML = '';
            
            // Ajouter les outils disponibles
            tools.forEach(tool => {
                const option = document.createElement('option');
                option.value = tool.name;
                option.textContent = tool.name;
                toolSelect.appendChild(option);
            });
            
            // Déclencher le changement pour afficher les paramètres du premier outil
            if (tools.length > 0) {
                toolSelect.dispatchEvent(new Event('change'));
            }
        } catch (error) {
            console.error('Erreur lors du chargement des outils disponibles:', error);
            resultContent.innerHTML = `<div class="error">Erreur lors du chargement des outils: ${error.message}</div>`;
        }
    }
    
    // Gérer le changement d'outil sélectionné
    toolSelect.addEventListener('change', function() {
        const selectedTool = tools.find(tool => tool.name === this.value);
        
        if (selectedTool) {
            // Afficher la description de l'outil
            toolDescription.textContent = selectedTool.description || '';
            
            // Générer les champs de paramètres dynamiquement
            paramFields.innerHTML = '';
            
            selectedTool.parameters.forEach(param => {
                const fieldDiv = document.createElement('div');
                fieldDiv.className = 'form-group';
                
                const label = document.createElement('label');
                label.setAttribute('for', param.name);
                label.textContent = `${param.name}${param.required ? ' *' : ''}: ${param.description || ''}`;
                
                const input = document.createElement('input');
                input.setAttribute('type', getInputType(param.type));
                input.setAttribute('id', param.name);
                input.setAttribute('name', param.name);
                
                if (param.required) {
                    input.setAttribute('required', 'required');
                }
                
                fieldDiv.appendChild(label);
                fieldDiv.appendChild(input);
                paramFields.appendChild(fieldDiv);
            });
        }
    });
    
    // Déterminer le type d'input en fonction du type de paramètre
    function getInputType(paramType) {
        switch(paramType.toLowerCase()) {
            case 'int':
            case 'integer':
            case 'float':
            case 'number':
                return 'number';
            case 'bool':
            case 'boolean':
                return 'checkbox';
            default:
                return 'text';
        }
    }
    
    // Gérer la soumission du formulaire
    toolForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Afficher l'indicateur de chargement
        loading.style.display = 'inline-block';
        
        // Réinitialiser les résultats précédents
        resultContent.className = '';
        resultContent.innerHTML = '<em>Traitement en cours...</em>';
        
        try {
            const toolName = toolSelect.value;
            const params = {};
            
            // Récupérer les valeurs des paramètres
            const selectedTool = tools.find(tool => tool.name === toolName);
            selectedTool.parameters.forEach(param => {
                const input = document.getElementById(param.name);
                if (input.type === 'checkbox') {
                    params[param.name] = input.checked;
                } else if (input.type === 'number') {
                    params[param.name] = parseFloat(input.value);
                } else {
                    params[param.name] = input.value;
                }
            });
            
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }
            
            const response = await fetch(`${apiUrl}/call_tool/`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    tool_name: toolName,
                    params: params
                })
            });
            
            // Cacher l'indicateur de chargement
            loading.style.display = 'none';
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Une erreur s\'est produite lors de l\'exécution de l\'outil.');
            }
            
            const data = await response.json();
            resultContent.className = 'success-result';
            resultContent.innerHTML = `<strong>Résultat :</strong> ${formatResult(data.result)}`;
        } catch (error) {
            // Cacher l'indicateur de chargement en cas d'erreur
            loading.style.display = 'none';
            
            // Afficher l'erreur
            resultContent.className = 'error-result';
            resultContent.innerHTML = `<strong>Erreur :</strong> ${error.message}`;
        }
    });
    
    // Formatter le résultat en fonction de son type
    function formatResult(result) {
        if (typeof result === 'object') {
            return '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
        }
        return result;
    }
    
    // Vérifier si l'authentification est requise au chargement de la page
    checkAuthRequired();
});