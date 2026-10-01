const API = 'https://vlfoqr98de.execute-api.us-east-1.amazonaws.com/api';

let historyChart;
let hourChart;

const el = (id) => document.getElementById(id);


function makeChart(canvas, type, labels, data, label) {
    return new Chart(canvas, {
        type,
        data: {
            labels,
            datasets: [{
                label,
                data,
                tension: 0.28,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#aebbd0'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#8191a8',
                        maxTicksLimit: 10
                    },
                    grid: {
                        color: '#1d2c42'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#8191a8'
                    },
                    grid: {
                        color: '#1d2c42'
                    }
                }
            }
        }
    });
}


function calcularEstado(personas, capacidad) {
    const porcentaje = (personas / capacidad) * 100;

    if (porcentaje > 100) {
        return 'EXCEDIDO';
    }

    if (porcentaje >= 100) {
        return 'COMPLETO';
    }

    if (porcentaje >= 80) {
        return 'PROXIMO';
    }

    return 'NORMAL';
}


function calcularEstadisticas(datos) {

    if (!datos.length) {
        return {
            promedio: 0,
            maximo: 0,
            superado: 0,
            total: 0
        };
    }

    const personas = datos.map(x => Number(x.personas) || 0);

    const promedio =
        personas.reduce((a, b) => a + b, 0) / personas.length;

    const maximo = Math.max(...personas);

    const superado = datos.filter(x => {
        const capacidad = Number(x.capacidad) || 25;
        return Number(x.personas) > capacidad;
    }).length;

    return {
        promedio: promedio.toFixed(1),
        maximo,
        superado,
        total: datos.length
    };
}


function calcularPromedioPorHora(datos) {

    const horas = {};

    datos.forEach(item => {

        const fecha = new Date(item.timestamp);
        const hora = fecha.getHours();

        if (!horas[hora]) {
            horas[hora] = [];
        }

        horas[hora].push(Number(item.personas) || 0);
    });

    return Object.keys(horas)
        .sort((a, b) => Number(a) - Number(b))
        .map(hora => {

            const valores = horas[hora];

            const promedio =
                valores.reduce((a, b) => a + b, 0) /
                valores.length;

            return {
                hora,
                promedio: Number(promedio.toFixed(1))
            };
        });
}


async function refresh() {

    try {

        // ==========================================
        // HISTÓRICO AWS
        // ==========================================

        const historicoResponse =
            await fetch(`${API}/historico`);

        if (!historicoResponse.ok) {
            throw new Error(
                `Error histórico: ${historicoResponse.status}`
            );
        }

        const datos = await historicoResponse.json();

        if (!Array.isArray(datos) || datos.length === 0) {
            throw new Error('No existen mediciones');
        }

        // Orden cronológico
        datos.sort(
            (a, b) =>
                new Date(a.timestamp) -
                new Date(b.timestamp)
        );

        // ==========================================
        // MEDICIÓN ACTUAL
        // ==========================================

        const current = datos[datos.length - 1];

        const personas =
            Number(current.personas) || 0;

        const capacidad =
            Number(current.capacidad) || 25;

        const ocupacion =
            Number(
                ((personas / capacidad) * 100).toFixed(1)
            );

        const estado =
            calcularEstado(personas, capacidad);

        el('apiStatus').textContent = 'API conectada';

        el('people').textContent = personas;
        el('capacity').textContent = capacidad;
        el('occupancy').textContent = `${ocupacion}%`;
        el('state').textContent =
            estado.replaceAll('_', ' ');

        el('origin').textContent =
            current.origen || 'REAL';


        // ==========================================
        // ESTADÍSTICAS
        // ==========================================

        const stats =
            calcularEstadisticas(datos);

        el('avg').textContent =
            stats.promedio;

        el('max').textContent =
            stats.maximo;

        el('exceeded').textContent =
            stats.superado;

        el('total').textContent =
            stats.total;


        // ==========================================
        // GRÁFICA HISTÓRICA
        // ==========================================

        const labels =
            datos.map(item =>
                new Date(
                    item.timestamp
                ).toLocaleString(
                    [],
                    {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                    }
                )
            );

        const values =
            datos.map(
                item =>
                    Number(item.personas) || 0
            );

        if (historyChart) {
            historyChart.destroy();
        }

        historyChart =
            makeChart(
                el('historyChart'),
                'line',
                labels,
                values,
                'Personas'
            );


        // ==========================================
        // PROMEDIO POR HORA
        // ==========================================

        const porHora =
            calcularPromedioPorHora(datos);

        const hourLabels =
            porHora.map(
                x => `${x.hora}:00`
            );

        const hourValues =
            porHora.map(
                x => x.promedio
            );

        if (hourChart) {
            hourChart.destroy();
        }

        hourChart =
            makeChart(
                el('hourChart'),
                'bar',
                hourLabels,
                hourValues,
                'Promedio'
            );


        // ==========================================
        // PREDICCIÓN IA AWS
        // ==========================================

        try {

            const prediccionResponse =
                await fetch(
                    `${API}/prediccion`
                );

            if (!prediccionResponse.ok) {
                throw new Error(
                    `Error predicción: ${prediccionResponse.status}`
                );
            }

            const prediccion =
                await prediccionResponse.json();

            console.log(
                'Predicción AWS:',
                prediccion
            );

            el('predNow').textContent =
                prediccion.personas_actuales;

            el('predFuture').textContent =
                prediccion.personas_estimadas;

            el('predPct').textContent =
                `${prediccion.ocupacion_estimada_porcentaje}%`;

            el('predState').textContent =
                prediccion.estado_estimado
                    .replaceAll('_', ' ');

            const mae =
                prediccion.metricas?.mae;

            if (mae !== undefined) {

                el('predModel').textContent =
                    `${prediccion.modelo} · MAE ${mae} personas`;

            } else {

                el('predModel').textContent =
                    prediccion.modelo;
            }

            el('predError').textContent = '';

        } catch (predictionError) {

            console.error(
                'Error en predicción:',
                predictionError
            );

            el('predNow').textContent =
                personas;

            el('predFuture').textContent =
                'Pendiente';

            el('predPct').textContent =
                'Pendiente';

            el('predState').textContent =
                'Pendiente';

            el('predModel').textContent =
                'RandomForestRegressor';

            el('predError').textContent =
                'No se pudo obtener la predicción AWS.';
        }

    } catch (error) {

        console.error(error);

        el('apiStatus').textContent =
            'API sin datos';
    }
}


// Primera carga
refresh();


// Actualización cada 10 segundos
setInterval(
    refresh,
    10000
);