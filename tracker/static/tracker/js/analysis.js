let cachedData = null;
let renderTimer = null;

let barView = null;
let pieView = null;

let selectedRange = null;
let selectedDate = null;

function getChartSizes() {
    const pieEl = document.getElementById("pieChart");
    const barEl = document.getElementById("barChart");

    const pieContainerWidth = pieEl ? pieEl.clientWidth : 420;
    const barContainerWidth = barEl ? barEl.clientWidth : 760;

    return {
        pieWidth: Math.min(420, pieContainerWidth - 16),
        pieHeight: 320,
        barWidth: Math.min(760, barContainerWidth - 16),
        barHeight: 340
    };
}

function buildPieSpec(filteredData, size) {
    return {
        $schema: "https://vega.github.io/schema/vega-lite/v5.json",
        background: "white",
        width: size.pieWidth,
        height: size.pieHeight,
        data: { values: filteredData || [] },

        transform: [
            {
                aggregate: [
                    { op: "sum", field: "kcal", as: "value" }
                ],
                groupby: ["macro"]
            },
            {
                calculate: "format(datum.value, '.0f') + ' kcal'",
                as: "labels"
            }
        ],

        layer: [
            // 1. donut
            {
                mark: {
                    type: "arc",
                    innerRadius: 40,
                    outerRadius: 140
                },
                encoding: {
                    theta: {
                        field: "value",
                        type: "quantitative"
                    },
                    color: {
                        field: "macro",
                        type: "nominal",
                        scale: {
                            domain: ["Protein", "Carbs", "Fat", "Fibre"],
                            range: ["#FE0000", "#00AACE", "#EEFF44", "#00CE00"]
                        },
                        legend: {
                            title: "",
                            symbolSize: 400,
                            rowPadding: 8,
                            labelFontWeight: "bold"
                        }
                    },
                    order: {
                        field: "macro",
                        type: "nominal",
                        sort: ["Protein", "Carbs", "Fat", "Fibre"]
                    },
                    tooltip: [
                        { field: "macro", type: "nominal", title: "Macro" },
                        { field: "value", type: "quantitative", title: "kcal", format: ".0f" }
                    ]
                }
            },

            // 2. arc labels
            {
                mark: {
                    type: "text",
                    radius: 105,
                    fontSize: 15,
                    fontWeight: "bold",
                    stroke: "gray",
                    strokeWidth: 0.1,
                    fill: "black"
                },
                encoding: {
                    theta: {
                        field: "value",
                        type: "quantitative",
                        stack: true
                    },
                    order: {
                        field: "macro",
                        type: "nominal",
                        sort: ["Protein", "Carbs", "Fat", "Fibre"]
                    },
                    text: {
                        field: "labels",
                        type: "nominal",
                    }
                }
            },

            // 3. center total
            {
                data: { values: filteredData || [] },
                transform: [
                    {
                        aggregate: [
                            { op: "sum", field: "kcal", as: "totalKcal" }
                        ]
                    }
                ],
                mark: {
                    type: "text",
                    align: "center",
                    baseline: "middle",
                    dy: -10,
                    fontSize: 24,
                    fontWeight: "bold"
                },
                encoding: {
                    text: {
                        field: "totalKcal",
                        type: "quantitative",
                        format: ".0f"
                    }
                }
            },

            // 4. center unit
            {
                data: { values: [{}] },
                mark: {
                    type: "text",
                    align: "center",
                    baseline: "middle",
                    dy: 14,
                    fontSize: 12
                },
                encoding: {
                    text: { value: "kcal" }
                }
            }
        ],

        view: { stroke: null }
    };
}
function buildBarSpec(barData, size) {
    const end = new Date();
    end.setHours(0, 0, 0, 0);

    const start = new Date(end);
    start.setDate(end.getDate() - 29);

    const axisValues = [];
    for (let i = 0; i < 30; i++) {
        const d = new Date(start);
        d.setDate(start.getDate() + i);
        axisValues.push(d.toISOString());
    }

    return {
        $schema: "https://vega.github.io/schema/vega-lite/v5.json",
        background: "white",
        width: size.barWidth,
        height: size.barHeight,
        data: { values: barData || [] },
        params: [
            {
                name: "dateBrush",
                select: {
                    type: "interval",
                    encodings: ["x"]
                }
            }
        ],
        mark: "bar",
        encoding: {
            x: {
                field: "date",
                type: "temporal",
                title: "Date",
                scale: {
                    domain: [start.toISOString(), end.toISOString()],
                    nice: false
                },
                axis: {
                    format: "%m-%d",
                    labelAngle: -30,
                    values: axisValues
                }
            },
            y: {
                field: "kcal",
                type: "quantitative",
                stack: "zero",
                title: "Calories (kcal)"
            },
            color: {
                field: "macro",
                type: "nominal",
                scale: {
                    domain: ["Protein", "Carbs", "Fat", "Fibre"],
                    range: ["#FE0000", "#00AACE", "#EEFF44", "#00CE00"]
                },
                legend: {
                    title: "",
                    symbolSize: 400,
                    rowPadding: 8,
                    labelFontWeight: "bold"
                }
            },
            opacity: {
                condition: { param: "dateBrush", value: 1 },
                value: 0.35
            },
            tooltip: [
                { field: "date", type: "temporal", title: "Date" },
                { field: "macro", type: "nominal", title: "Macro" },
                { field: "kcal", type: "quantitative", title: "Macro kcal" },
                { field: "dailyCalories", type: "quantitative", title: "Daily total kcal" }
            ]
        },
        view: { stroke: null }
    };
}

function normalizeDateOnly(value) {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return null;

    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

function normalizeBrushRange(range) {
    if (!range || !Array.isArray(range) || range.length !== 2) {
        return null;
    }

    const start = new Date(range[0]);
    const end = new Date(range[1]);

    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
        return null;
    }

    return [start.getTime(), end.getTime()];
}

function extractRangeFromBrushSignal(value) {
    if (!value) return null;

    if (Array.isArray(value.date) && value.date.length === 2) {
        return value.date;
    }

    if (Array.isArray(value) && value.length === 2) {
        return value;
    }

    return null;
}

function filterData(data) {
    if (!Array.isArray(data)) return [];

    if (selectedDate) {
        const selectedDayMs = normalizeDateOnly(selectedDate);
        if (selectedDayMs === null) return data;

        return data.filter((row) => {
            const rowDayMs = normalizeDateOnly(row.date);
            return rowDayMs === selectedDayMs;
        });
    }

    const normalizedRange = normalizeBrushRange(selectedRange);
    if (normalizedRange) {
        const [startMs, endMs] = normalizedRange;

        return data.filter((row) => {
            const rowMs = new Date(row.date).getTime();
            if (Number.isNaN(rowMs)) return false;
            return rowMs >= startMs && rowMs <= endMs;
        });
    }

    return data;
}

async function renderPieChart() {
    if (!cachedData) return;

    const size = getChartSizes();
    const filteredData = filterData(cachedData.barData);

    if (pieView) {
        pieView.finalize();
        pieView = null;
    }

    const result = await vegaEmbed(
        "#pie-chart",
        buildPieSpec(filteredData, size),
        { actions: false }
    );

    pieView = result.view;
}

function getAvailableSignalNames(view) {
    try {
        const signals = view.getState().signals || {};
        return Object.keys(signals);
    } catch (err) {
        console.warn("Unable to inspect signals:", err);
        return [];
    }
}

function findBrushSignalName(view) {
    const signalNames = getAvailableSignalNames(view);

    const candidates = [
        "dateBrush",
        "dateBrush_tuple",
        "dateBrush_x"
    ];

    for (const name of candidates) {
        if (signalNames.includes(name)) {
            return name;
        }
    }

    return signalNames.find((name) => name.startsWith("dateBrush")) || null;
}

async function bindBarInteractions() {
    if (!barView) return;

    const brushSignalName = findBrushSignalName(barView);

    if (brushSignalName) {
        barView.addSignalListener(brushSignalName, async (_, value) => {
            const range = extractRangeFromBrushSignal(value);
            selectedRange = range;

            if (range) {
                selectedDate = null;
            }

            await renderPieChart();
        });
    } else {
        console.warn("No dateBrush signal found.");
    }

    barView.addEventListener("click", async (event, item) => {
        const datum = item && item.datum;

        if (datum && datum.date) {
            selectedDate = datum.date;
            selectedRange = null;
            await renderPieChart();
            return;
        }

        selectedDate = null;
        await renderPieChart();
    });

    barView.addEventListener("dblclick", async () => {
        selectedDate = null;
        selectedRange = null;
        await renderPieChart();
    });
}

async function restoreBarBrush() {
    if (!barView || !selectedRange) return;

    const brushSignalName = findBrushSignalName(barView);
    if (!brushSignalName) return;

    try {
        await barView.signal(brushSignalName, { date: selectedRange }).runAsync();
    } catch (err) {
        console.warn("Failed to restore brush:", err);
    }
}

async function renderBarChart() {
    if (!cachedData) return;

    const size = getChartSizes();

    if (barView) {
        barView.finalize();
        barView = null;
    }

    const result = await vegaEmbed(
        "#bar-chart",
        buildBarSpec(cachedData.barData, size),
        { actions: false }
    );

    barView = result.view;

    await bindBarInteractions();
    await restoreBarBrush();
}

async function renderCharts() {
    await renderBarChart();
    await renderPieChart();
}

async function loadCharts() {
    const response = await fetch("/api/analysis/", {
        method: "GET",
        headers: {
            "Accept": "application/json"
        },
        credentials: "same-origin"
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    cachedData = await response.json();
    await renderCharts();
}

function scheduleRerender() {
    if (!cachedData) return;

    clearTimeout(renderTimer);
    renderTimer = setTimeout(() => {
        renderCharts().catch((err) => {
            console.error("Failed to rerender charts:", err);
        });
    }, 120);
}

loadCharts().catch((err) => {
    console.error("Failed to load charts:", err);
});

window.addEventListener("resize", scheduleRerender);

const chartsEl = document.getElementById("charts");
if (chartsEl) {
    const resizeObserver = new ResizeObserver(() => {
        scheduleRerender();
    });
    resizeObserver.observe(chartsEl);
}