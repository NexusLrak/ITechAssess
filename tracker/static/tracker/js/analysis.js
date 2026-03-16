let cachedData = null;
let renderTimer = null;

let barView = null;
let pieView = null;

const params = new URLSearchParams(window.location.search);
const selected_date = params.get("date")

function applyTheme() {
    const theme = localStorage.getItem("theme");

    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    } else {
        document.documentElement.removeAttribute("data-theme");
    }
}

applyTheme();

window.addEventListener("message", function (event) {

    if (event.data === "themeChanged") {

        applyTheme();

        if (typeof renderCharts === "function") {
            renderCharts();
        }
    }

});

function isDarkMode() {
    return localStorage.getItem("theme") === "dark";
}

function getTextColor() {
    return isDarkMode() ? "#e6f1ec" : "#34495e";
}

function getGridColor() {
    return isDarkMode() ? "#3c4744" : "#e9ecef";
}

function getBgColor() {
    return isDarkMode() ? "#1f2624" : "#ffffff";
}

function getChartSizes() {
    const pieEl = document.getElementById("pieChart");
    const barEl = document.getElementById("barChart");

    const pieWidth = pieEl ? pieEl.clientWidth : 400;
    const pieHeight = pieEl ? pieEl.clientHeight : 320;

    const barWidth = barEl ? barEl.clientWidth : 700;
    const barHeight = barEl ? barEl.clientHeight : 340;

    return {
        pieWidth,
        pieHeight,
        barWidth,
        barHeight
    };
}

function getTodayRange() {
    const start = new Date(selected_date);
    start.setHours(0,0,0,0);

    const end = new Date();
    end.setHours(23,59,59,999);

    return { start, end };
}

function getCurrentWeekRange() {
    const today = new Date(selected_date);
    const day = today.getDay();

    const diffToMonday = day === 0 ? 6 : day - 1;

    const start = new Date(today);
    start.setHours(0,0,0,0);
    start.setDate(today.getDate() - diffToMonday);

    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    end.setHours(23,59,59,999);

    return { start, end };
}

function filterByRange(data, start, end) {
    if (!Array.isArray(data)) return [];

    const startMs = start.getTime();
    const endMs = end.getTime();

    return data.filter(row => {
        const d = new Date(row.date);
        const ms = d.getTime();
        return !Number.isNaN(ms) && ms >= startMs && ms <= endMs;
    });
}

function filterCurrentWeek(data) {
    const { start, end } = getCurrentWeekRange();

    const startStr = start.toISOString().slice(0, 10);
    const endStr = end.toISOString().slice(0, 10);

    return data.filter((row) => {
        return row.date >= startStr && row.date <= endStr;
    });
}

function filterCurrentWeek(data) {
    const {start,end} = getCurrentWeekRange();
    return filterByRange(data,start, end);
}

function filterToday(data) {
    const {start,end} = getTodayRange();
    return filterByRange(data,start, end);
}

function hasKcalData(data) {
    return Array.isArray(data) && data.some((row) => {
        const kcal = Number(row.kcal);
        return !Number.isNaN(kcal) && kcal > 0;
    });
}

function buildPieSpec(filteredData, size) {
    const radius = 120;

    return {
        $schema: "https://vega.github.io/schema/vega-lite/v5.json",
        autosize: {
            type: "fit",
            contains: "padding"
        },
        background: getBgColor(),
        width: "container",
        height: 320,
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
            {
                mark: {
                    type: "arc",
                    innerRadius: radius * 0.35,
                    outerRadius: radius
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
                            domain: ["Protein", "Carbs", "Fat"],
                            range: ["#d16b6b", "#6fa8dc", "#e5c07b"]
                        },
                        legend: {
                            title: "",
                            symbolSize: 400,
                            rowPadding: 8,
                            labelFontWeight: "bold",
                            labelColor: getTextColor(),
                            titleColor: getTextColor()
                        }
                    },
                    order: {
                        field: "macro",
                        type: "nominal",
                        sort: ["Protein", "Carbs", "Fat"]
                    },
                    tooltip: [
                        { field: "macro", type: "nominal", title: "Macro" },
                        { field: "value", type: "quantitative", title: "kcal", format: ".0f" }
                    ]
                }
            },
            {
                mark: {
                    type: "text",
                    radius: 105,
                    fontSize: 15,
                    fontWeight: "bold",
                    stroke: "gray",
                    strokeWidth: 0.1,
                    fill: getTextColor()
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
                        sort: ["Protein", "Carbs", "Fat"]
                    },
                    text: {
                        field: "labels",
                        type: "nominal"
                    }
                }
            },
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
                    fontWeight: "bold",
                    fill: getTextColor()
                },
                encoding: {
                    text: {
                        field: "totalKcal",
                        type: "quantitative",
                        format: ".0f"
                    }
                }
            },
            {
                data: { values: [{}] },
                mark: {
                    type: "text",
                    align: "center",
                    baseline: "middle",
                    dy: 14,
                    fontSize: 12,
                    fill: getTextColor()
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
    const { start, end } = getCurrentWeekRange();

    const axisLabels = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(start);
        d.setDate(start.getDate() + i);

        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        axisLabels.push(`${yyyy}-${mm}-${dd}`);
    }

    return {
        $schema: "https://vega.github.io/schema/vega-lite/v5.json",
        autosize: {
            type: "fit",
            contains: "padding"
        },
        background: getBgColor(),
        width: "container",
        height: 340,
        data: { values: filterCurrentWeek(barData) },

        layer: [
            {
                transform: [
                    {
                        timeUnit: "yearmonthdate",
                        field: "date",
                        as: "day"
                    },
                    {
                        calculate: "timeFormat(datum.day, '%Y-%m-%d')",
                        as: "dayKey"
                    },
                    {
                        calculate: "timeFormat(datum.day, '%m-%d')",
                        as: "dayLabel"
                    },
                    {
                        aggregate: [
                            { op: "sum", field: "kcal", as: "kcal" }
                        ],
                        groupby: ["dayKey", "dayLabel", "macro"]
                    }
                ],
                mark: {
                    type: "bar"
                },
                encoding: {
                    x: {
                        field: "dayKey",
                        type: "ordinal",
                        title: "Date",
                        sort: axisLabels,
                        scale: {
                            paddingInner: 0.08,
                            paddingOuter: 0.22
                        },
                        axis: {
                            labelAngle: -30,
                            labelColor: getTextColor(),
                            titleColor: getTextColor(),
                            domainColor: getGridColor(),
                            tickColor: getGridColor(),
                            labelExpr: "substring(datum.label, 5, 10)"
                        }
                    },
                    y: {
                        field: "kcal",
                        type: "quantitative",
                        stack: "zero",
                        title: "Calories (kcal)",
                        axis: {
                            labelColor: getTextColor(),
                            titleColor: getTextColor(),
                            gridColor: getGridColor(),
                            domainColor: getGridColor(),
                            tickColor: getGridColor()
                        }
                    },
                    color: {
                        field: "macro",
                        type: "nominal",
                        scale: {
                            domain: ["Protein", "Carbs", "Fat"],
                            range: ["#d16b6b", "#6fa8dc", "#e5c07b"]
                        },
                        legend: {
                            title: "",
                            symbolSize: 400,
                            rowPadding: 8,
                            labelFontWeight: "bold",
                            labelColor: getTextColor(),
                            titleColor: getTextColor()
                        }
                    },
                    tooltip: [
                        { field: "dayLabel", type: "nominal", title: "Date" },
                        { field: "macro", type: "nominal", title: "Macro" },
                        { field: "kcal", type: "quantitative", title: "Macro kcal", format: ".0f" }
                    ]
                }
            },
            {
                transform: [
                    {
                        timeUnit: "yearmonthdate",
                        field: "date",
                        as: "day"
                    },
                    {
                        calculate: "timeFormat(datum.day, '%Y-%m-%d')",
                        as: "dayKey"
                    },
                    {
                        calculate: "timeFormat(datum.day, '%m-%d')",
                        as: "dayLabel"
                    },
                    {
                        aggregate: [
                            { op: "sum", field: "kcal", as: "totalKcal" }
                        ],
                        groupby: ["dayKey", "dayLabel"]
                    },
                    {
                        calculate: "format(datum.totalKcal, '.0f') + ' kcal'",
                        as: "totalLabel"
                    }
                ],
                mark: {
                    type: "text",
                    dy: -8,
                    fontSize: 13,
                    fontWeight: "bold",
                    fill: getTextColor()
                },
                encoding: {
                    x: {
                        field: "dayKey",
                        type: "ordinal",
                        sort: axisLabels
                    },
                    y: {
                        field: "totalKcal",
                        type: "quantitative"
                    },
                    text: {
                        field: "totalLabel",
                        type: "nominal"
                    }
                }
            }
        ],

        view: { stroke: null }
    };
}

async function renderPieChart() {
    if (!cachedData) return;

    const pieContainer = document.getElementById("pie-chart");
    if (!pieContainer) return;

    const size = getChartSizes();
    const filteredData = filterToday(cachedData.barData);

    if (pieView) {
        pieView.finalize();
        pieView = null;
    }

    if (!hasKcalData(filteredData)) {
        pieContainer.innerHTML = `
            <div style="
                width: 100%;
                height: 320px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: ${getTextColor()};
                background: ${getBgColor()};
                font-size: 18px;
                font-weight: 600;
            ">
                No data today
            </div>
        `;
        return;
    }

    pieContainer.innerHTML = "";

    const result = await vegaEmbed(
        "#pie-chart",
        buildPieSpec(filteredData, size),
        {
            actions: false,
            renderer: "svg"
        }
    );

    pieView = result.view;
}

async function renderBarChart() {
    if (!cachedData) return;


    const barContainer = document.getElementById("bar-chart");
    if (!barContainer) return;

    const size = getChartSizes();

    if (barView) {
        barView.finalize();
        barView = null;
    }

    const filteredData = filterCurrentWeek(cachedData.barData);
        
    if (!hasKcalData(filteredData)) {
        barContainer.innerHTML = `
            <div style="
                width: 100%;
                height: 320px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: ${getTextColor()};
                background: ${getBgColor()};
                font-size: 18px;
                font-weight: 600;
            ">
                No data this week
            </div>
        `;
    return;
    }

    const result = await vegaEmbed(
        "#bar-chart",
        buildBarSpec(filteredData, size),
        {
            actions: false,
            renderer: "svg"
        }
    );

    barView = result.view;
}

async function renderCharts() {
    await renderBarChart();
    await renderPieChart();
}

async function loadCharts() {
    const response = await fetch("/api/analysis/?date="+selected_date, {
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

window.addEventListener("message", (event) => {
    if (event.data === "themeChanged") {
        renderCharts().catch((err) => {
            console.error("Failed to rerender charts after theme change:", err);
        });
    }
});