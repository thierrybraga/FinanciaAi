document.addEventListener('DOMContentLoaded', () => {
    // --- Lógica Geral para Todas as Páginas ---

    // Lógica para o menu hamburguer
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navList = document.querySelector('.nav-list');

    if (navbarToggler && navList) {
        navbarToggler.addEventListener('click', () => {
            const isExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
            navbarToggler.setAttribute('aria-expanded', !isExpanded);
            navList.classList.toggle('active');
        });
    }

    // Lógica para fechar mensagens flash
    document.querySelectorAll('.flash-messages .dismiss').forEach(button => {
        button.addEventListener('click', (event) => {
            const alertMessage = event.target.closest('.alert-message');
            if (alertMessage) {
                alertMessage.remove();
            }
        });
    });


    // --- Lógica Específica para a Página de Adicionar Financeira ---
    // Verifica se a seção de adicionar empresa está presente na página
    if (document.querySelector('.add-company-section')) {
        // === Funções de Máscara de Input ===
        const applyCnpjMask = (input) => {
            input.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
                if (value.length > 14) value = value.slice(0, 14); // Limita a 14 dígitos

                if (value.length > 12) {
                    value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
                } else if (value.length > 8) {
                    value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{0,4})$/, '$1.$2.$3/$4');
                } else if (value.length > 5) {
                    value = value.replace(/^(\d{2})(\d{3})(\d{0,3})$/, '$1.$2.$3');
                } else if (value.length > 2) {
                    value = value.replace(/^(\d{2})(\d{0,3})$/, '$1.$2');
                }
                e.target.value = value;
            });
        };

        const applyPhoneMask = (input) => {
            input.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
                // Ajustado para lidar com números de 10 (sem nono dígito) ou 11 dígitos (com nono dígito)
                if (value.length > 11) value = value.slice(0, 11);

                // Formato para 11 dígitos (com DDD e 9 na frente): (XX) 9XXXX-XXXX
                if (value.length === 11) {
                    value = value.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
                }
                // Formato para 10 dígitos (com DDD e sem 9 na frente): (XX) XXXX-XXXX
                else if (value.length === 10) {
                    value = value.replace(/^(\d{2})(\d{4})(\d{4})$/, '($1) $2-$3');
                }
                // Formatos parciais
                else if (value.length > 6) {
                    value = value.replace(/^(\d{2})(\d{4})(\d{0,4})$/, '($1) $2-$3');
                } else if (value.length > 2) {
                    value = value.replace(/^(\d{2})(\d{0,4})$/, '($1) $2');
                }
                e.target.value = value;
            });
        };

        // Aplicar máscaras aos campos específicos
        const cnpjInput = document.getElementById('cnpj');
        if (cnpjInput) {
            applyCnpjMask(cnpjInput);
        }

        const contactPhoneInput = document.getElementById('contact_phone');
        if (contactPhoneInput) {
            applyPhoneMask(contactPhoneInput);
        }

        // === Validação de Formulário em Tempo Real ===
        const form = document.getElementById('add-company-form');
        if (form) {
            const inputs = form.querySelectorAll('.form-control[required]');
            const countrySelect = document.getElementById('country');

            // Função para validar um input específico
            const validateInput = (input) => {
                const formGroup = input.closest('.form-group');
                let isValid = true;
                let errorMessage = '';

                if (input.type === 'email') {
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailPattern.test(input.value.trim())) {
                        isValid = false;
                        errorMessage = 'Por favor, insira um endereço de e-mail válido.';
                    }
                }

                if (isValid && !input.value.trim()) {
                    isValid = false;
                    errorMessage = 'Este campo é obrigatório.';
                }

                if (isValid && input.hasAttribute('pattern') && input.value.trim()) {
                    const pattern = new RegExp(input.getAttribute('pattern'));
                    if (!pattern.test(input.value.trim())) {
                        isValid = false;
                        errorMessage = input.dataset.tooltip || 'Formato inválido.';
                    }
                }

                if (isValid) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                    removeErrorMessage(formGroup, input.id + '-error');
                } else {
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                    displayErrorMessage(formGroup, input.id + '-error', errorMessage);
                }
                return isValid;
            };

            // Função auxiliar para exibir mensagem de erro
            const displayErrorMessage = (formGroup, id, message) => {
                let errorElement = document.getElementById(id);
                if (!errorElement) {
                    errorElement = document.createElement('small');
                    errorElement.id = id;
                    errorElement.classList.add('form-text', 'alert-error');
                    errorElement.setAttribute('role', 'alert');
                    errorElement.setAttribute('aria-live', 'assertive');
                    formGroup.appendChild(errorElement);
                }
                errorElement.innerHTML = message;
            };

            // Função auxiliar para remover mensagem de erro
            const removeErrorMessage = (formGroup, id) => {
                const errorElement = document.getElementById(id);
                if (errorElement) {
                    errorElement.remove();
                }
            };

            inputs.forEach(input => {
                input.addEventListener('blur', () => validateInput(input));
                input.addEventListener('input', () => {
                    input.classList.remove('is-invalid', 'is-valid');
                    const formGroup = input.closest('.form-group');
                    removeErrorMessage(formGroup, input.id + '-error');
                });
            });

            if (countrySelect) {
                const validateCountrySelect = () => {
                    const formGroup = countrySelect.closest('.form-group');
                    let isValid = true;
                    let errorMessage = '';

                    if (!countrySelect.value) {
                        isValid = false;
                        errorMessage = 'Por favor, selecione um país.';
                    }

                    if (isValid) {
                        countrySelect.classList.remove('is-invalid');
                        countrySelect.classList.add('is-valid');
                        removeErrorMessage(formGroup, countrySelect.id + '-error');
                    } else {
                        countrySelect.classList.add('is-invalid');
                        countrySelect.classList.remove('is-valid');
                        displayErrorMessage(formGroup, countrySelect.id + '-error', errorMessage);
                    }
                    return isValid;
                };
                countrySelect.addEventListener('change', validateCountrySelect);
                countrySelect.addEventListener('blur', validateCountrySelect);
                validateCountrySelect(); // Initial validation check
            }

            form.addEventListener('submit', (e) => {
                let formIsValid = true;
                inputs.forEach(input => {
                    if (!validateInput(input)) {
                        formIsValid = false;
                    }
                });

                if (countrySelect && !validateCountrySelect()) {
                    formIsValid = false;
                }

                if (!formIsValid) {
                    e.preventDefault();
                    const firstInvalid = form.querySelector('.is-invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            });
        }
    }


    // --- Lógica Específica para a Página de Simulação de Empréstimo ---
    // Verifica se a seção de simulação de empréstimo está presente na página
    if (document.querySelector('.loan-simulation-section')) {
        // Função utilitária para formatar moeda
        const formatCurrency = (value) => {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value);
        };

        const summaryDataElement = document.getElementById('summary-data');
        if (summaryDataElement) {
            try {
                // Assume que os dados são armazenados como uma string JSON em um atributo data
                const summaryData = JSON.parse(summaryDataElement.textContent);

                // Variáveis para os gráficos
                const months = summaryData.amortization_schedule.map(item => item.month);
                const principalBalances = summaryData.amortization_schedule.map(item => item.remaining_balance);
                const interests = summaryData.amortization_schedule.map(item => item.interest_paid);
                const amortizations = summaryData.amortization_schedule.map(item => item.amortized_value);
                const totalInstallment = summaryData.amortization_schedule.map(item => item.installment_value);

                // --- Gráficos (Chart.js) ---
                // Gráfico 1: Saldo Devedor ao Longo do Tempo (Line Chart)
                const balanceCtx = document.getElementById('balanceChart');
                if (balanceCtx) {
                    new Chart(balanceCtx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: months,
                            datasets: [{
                                label: 'Saldo Devedor (R$)',
                                data: principalBalances,
                                borderColor: '#007bff',
                                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                tension: 0.1,
                                fill: true,
                                pointRadius: 3,
                                pointBackgroundColor: '#007bff',
                                pointBorderColor: '#fff',
                                pointHoverRadius: 5
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' },
                                title: { display: true, text: 'Evolução do Saldo Devedor' },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: { title: { display: true, text: 'Mês' } },
                                y: {
                                    title: { display: true, text: 'Saldo (R$)' },
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) { return formatCurrency(value); }
                                    }
                                }
                            }
                        }
                    });
                }

                // Gráfico 2: Juros Pagos por Mês (Line Chart)
                const interestCtx = document.getElementById('interestChart');
                if (interestCtx) {
                    new Chart(interestCtx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: months,
                            datasets: [{
                                label: 'Juros Pagos (R$)',
                                data: interests,
                                borderColor: '#dc3545',
                                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                tension: 0.1,
                                fill: true,
                                pointRadius: 3,
                                pointBackgroundColor: '#dc3545',
                                pointBorderColor: '#fff',
                                pointHoverRadius: 5
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' },
                                title: { display: true, text: 'Juros Pagos por Mês' },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                // Gráfico 3: Amortização do Principal por Mês (Line Chart)
                const amortizationCtx = document.getElementById('amortizationChart');
                if (amortizationCtx) {
                    new Chart(amortizationCtx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: months,
                            datasets: [{
                                label: 'Valor Amortizado (R$)',
                                data: amortizations,
                                borderColor: '#28a745',
                                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                tension: 0.1,
                                fill: true,
                                pointRadius: 3,
                                pointBackgroundColor: '#28a745',
                                pointBorderColor: '#fff',
                                pointHoverRadius: 5
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' },
                                title: { display: true, text: 'Amortização do Principal por Mês' },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                // Gráfico 4: Parcela Total por Mês (Line Chart)
                const totalInstallmentCtx = document.getElementById('totalInstallmentChart');
                if (totalInstallmentCtx) {
                    new Chart(totalInstallmentCtx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: months,
                            datasets: [{
                                label: 'Parcela Total (R$)',
                                data: totalInstallment,
                                borderColor: '#ffc107',
                                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                                tension: 0.1,
                                fill: true,
                                pointRadius: 3,
                                pointBackgroundColor: '#ffc107',
                                pointBorderColor: '#fff',
                                pointHoverRadius: 5
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' },
                                title: { display: true, text: 'Parcela Total por Mês' },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                // Gráfico 5: Proporção Total (Principal vs. Juros) - Pie Chart
                const totalProportionCtx = document.getElementById('totalProportionChart');
                if (totalProportionCtx) {
                    new Chart(totalProportionCtx.getContext('2d'), {
                        type: 'pie',
                        data: {
                            labels: ['Principal Total', 'Juros Total'],
                            datasets: [{
                                data: [summaryData.total_principal, summaryData.total_interest],
                                backgroundColor: ['#17a2b8', '#fd7e14'],
                                hoverOffset: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: true, position: 'top' },
                                title: { display: true, text: 'Proporção Total: Principal vs. Juros' },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            const value = parseFloat(context.parsed);
                                            const total = parseFloat(summaryData.total_principal) + parseFloat(summaryData.total_interest);
                                            const percentage = (value / total * 100).toFixed(2);
                                            return `${context.label}: ${formatCurrency(value)} (${percentage}%)`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                // --- Lógica para alternar a visibilidade dos gráficos ---
                const chartNavButtons = document.querySelector('.chart-nav-buttons');
                const chartContainers = document.querySelectorAll('.chart-container');

                if (chartNavButtons && chartContainers.length > 0) {
                    chartNavButtons.addEventListener('click', function(event) {
                        const targetButton = event.target.closest('.btn');
                        if (targetButton && targetButton.dataset.chart) {
                            chartNavButtons.querySelectorAll('.btn').forEach(btn => {
                                btn.classList.remove('active');
                                btn.setAttribute('aria-selected', 'false');
                            });

                            targetButton.classList.add('active');
                            targetButton.setAttribute('aria-selected', 'true');

                            chartContainers.forEach(container => {
                                container.classList.add('hidden');
                                container.setAttribute('aria-hidden', 'true');
                            });

                            const chartIdToShow = targetButton.dataset.chart;
                            const chartToShow = document.getElementById(chartIdToShow).closest('.chart-container');
                            if (chartToShow) {
                                chartToShow.classList.remove('hidden');
                                chartToShow.setAttribute('aria-hidden', 'false');
                            }
                        }
                    });

                    // Ativar o primeiro botão e mostrar o primeiro gráfico por padrão
                    const firstButton = chartNavButtons.querySelector('.btn');
                    if (firstButton) {
                        firstButton.classList.add('active');
                        firstButton.setAttribute('aria-selected', 'true');
                        const firstChartContainer = document.getElementById(firstButton.dataset.chart).closest('.chart-container');
                        if (firstChartContainer) {
                            firstChartContainer.classList.remove('hidden');
                            firstChartContainer.setAttribute('aria-hidden', 'false');
                        }
                    }
                }

                // --- Lógica para paginação da tabela de amortização ---
                const amortizationTableBody = document.getElementById('amortizationTableBody');
                const prevPageBtn = document.getElementById('prevPageBtn');
                const nextPageBtn = document.getElementById('nextPageBtn');
                const currentPageSpan = document.getElementById('currentPage');
                const totalPagesSpan = document.getElementById('totalPages');
                const rowsPerPage = 10;
                let currentPage = 1;

                if (amortizationTableBody && prevPageBtn && nextPageBtn && currentPageSpan && totalPagesSpan) {
                    const allRows = summaryData.amortization_schedule;
                    const totalPages = Math.ceil(allRows.length / rowsPerPage);

                    const renderTable = (page) => {
                        amortizationTableBody.innerHTML = '';
                        const start = (page - 1) * rowsPerPage;
                        const end = start + rowsPerPage;
                        const rowsToDisplay = allRows.slice(start, end);

                        rowsToDisplay.forEach(item => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td data-label="Mês">${item.month}</td>
                                <td data-label="Parcela">${formatCurrency(item.installment_value)}</td>
                                <td data-label="Juros">${formatCurrency(item.interest_paid)}</td>
                                <td data-label="Amortizado">${formatCurrency(item.amortized_value)}</td>
                                <td data-label="Saldo Devedor">${formatCurrency(item.remaining_balance)}</td>
                            `;
                            amortizationTableBody.appendChild(row);
                        });

                        currentPageSpan.textContent = page;
                        totalPagesSpan.textContent = totalPages;

                        prevPageBtn.disabled = page === 1;
                        nextPageBtn.disabled = page === totalPages;
                    };

                    prevPageBtn.addEventListener('click', () => {
                        if (currentPage > 1) {
                            currentPage--;
                            renderTable(currentPage);
                        }
                    });

                    nextPageBtn.addEventListener('click', () => {
                        if (currentPage < totalPages) {
                            currentPage++;
                            renderTable(currentPage);
                        }
                    });

                    renderTable(currentPage);
                }

                // --- Lógica para o comprometimento de renda (Gráfico de Rosca) ---
                const incomeCommitmentChartCtx = document.getElementById('incomeCommitmentChart');
                let incomeCommitmentChartInstance = null; // Para armazenar a instância do Chart.js

                const monthlyIncomeInput = document.getElementById('monthly_income');
                const firstInstallmentElement = document.getElementById('firstInstallmentValue');
                const minIncomeSuggestionSpan = document.getElementById('minIncomeSuggestion');

                const updateIncomeCommitmentChart = () => {
                    if (!incomeCommitmentChartCtx || !firstInstallmentElement) return;

                    const monthlyIncome = parseFloat(monthlyIncomeInput.value) || 0;
                    const firstInstallmentText = firstInstallmentElement.textContent;
                    const firstInstallment = parseFloat(firstInstallmentText.replace(/[R$\s.]/g, '').replace(',', '.')) || 0;

                    const minSuggestedIncome = (firstInstallment / 0.30); // 30% de comprometimento
                    minIncomeSuggestionSpan.textContent = formatCurrency(minSuggestedIncome);

                    let committedPercentage = 0;
                    let remainingPercentage = 100;

                    if (monthlyIncome > 0) {
                        committedPercentage = (firstInstallment / monthlyIncome) * 100;
                        if (committedPercentage > 100) committedPercentage = 100;
                        remainingPercentage = 100 - committedPercentage;
                    }

                    const chartData = {
                        labels: ['Renda Comprometida', 'Renda Disponível'],
                        datasets: [{
                            data: [committedPercentage, remainingPercentage],
                            backgroundColor: [
                                committedPercentage > 30 ? '#dc3545' : '#17a2b8',
                                '#28a745'
                            ],
                            hoverOffset: 4
                        }]
                    };

                    if (incomeCommitmentChartInstance) {
                        incomeCommitmentChartInstance.data = chartData;
                        incomeCommitmentChartInstance.update();
                    } else {
                        incomeCommitmentChartInstance = new Chart(incomeCommitmentChartCtx.getContext('2d'), {
                            type: 'doughnut',
                            data: chartData,
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: true, position: 'top' },
                                    title: { display: true, text: 'Comprometimento Mensal da Renda' },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                return `${context.label}: ${context.parsed.toFixed(2)}%`;
                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }
                };

                monthlyIncomeInput.addEventListener('input', updateIncomeCommitmentChart);
                updateIncomeCommitmentChart(); // Inicializa o gráfico

                // --- Lógica para o botão "Gerar Relatório PDF" ---
                const generatePdfBtn = document.getElementById('generatePdfBtn');
                if (generatePdfBtn) {
                    generatePdfBtn.addEventListener('click', function() {
                        alert('Funcionalidade de Gerar Relatório PDF em desenvolvimento!');
                    });
                }

                // --- Lógica para o botão "Recalcular" ---
                const recalculateBtn = document.getElementById('recalculateBtn');
                if (recalculateBtn) {
                    recalculateBtn.addEventListener('click', function() {
                        window.location.href = window.location.pathname;
                    });
                }

            } catch (e) {
                console.error("Erro ao analisar dados do resumo ou inicializar gráficos:", e);
            }
        } else {
            console.warn("Elemento 'summary-data' não encontrado. Gráficos não serão inicializados.");
        }
    }
});