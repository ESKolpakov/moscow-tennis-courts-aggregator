// Здесь логика для AJAX-запросов, обновления статусов,
// применения фильтров без перезагрузки страницы и т.п.

console.log("Moscow Tennis Slots UI loaded");

// Запрос слотов из API с учётом фильтров
async function fetchSlots(filters = {}) {
    const url = new URL("/api/slots", window.location.origin);

    // Добавляем только непустые параметры
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            url.searchParams.append(key, value);
        }
    });

    const response = await fetch(url.toString(), {
        headers: {
            "Accept": "application/json"
        }
    });

    if (!response.ok) {
        throw new Error("Ошибка при загрузке слотов");
    }

    const data = await response.json();
    return data.slots || [];
}

// Перерисовываем tbody таблицы
function renderSlots(slots) {
    const tbody = document.getElementById("slots-table-body");
    if (!tbody) {
        console.warn("Не найден элемент slots-table-body");
        return;
    }

    if (!slots.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    Нет слотов для отображения
                </td>
            </tr>
        `;
        return;
    }

    const rowsHtml = slots
        .map((slot) => {
            const statusBadge =
                slot.status === "free"
                    ? '<span class="badge bg-success">Свободен</span>'
                    : '<span class="badge bg-secondary">Занят</span>';

            const source = slot.source || "";

            return `
                <tr>
                    <td>${slot.date}</td>
                    <td>${slot.time_range}</td>
                    <td>${slot.duration_minutes} мин</td>
                    <td>${slot.club}</td>
                    <td>${slot.court}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <span class="badge bg-light text-muted border">
                            ${source}
                        </span>
                    </td>
                </tr>
            `;
        })
        .join("");

    tbody.innerHTML = rowsHtml;
}

// Подписываемся на события после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    const refreshBtn = document.getElementById("refresh-slots-btn");
    const form = document.getElementById("filters-form");
    const applyBtn = document.getElementById("apply-filters-btn");
    const resetBtn = document.getElementById("reset-filters-btn");
    const freeOnlyCheckbox = document.getElementById("freeOnly");

    // Кнопка "Обновить статусы" (просто тянет /api/slots без фильтров)
    if (refreshBtn) {
        refreshBtn.addEventListener("click", async () => {
            const originalText = refreshBtn.textContent;
            refreshBtn.disabled = true;
            refreshBtn.textContent = "Обновляем...";

            try {
                const slots = await fetchSlots();
                renderSlots(slots);
            } catch (error) {
                console.error(error);
                alert("Не удалось обновить слоты. Попробуйте позже.");
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.textContent = originalText;
            }
        });
    }

    if (!form) {
        return;
    }

    // Собираем значения фильтров из формы
    const collectFilters = () => {
        const filters = {
            date: form.elements["date"].value,
            time_from: form.elements["time_from"].value,
            time_to: form.elements["time_to"].value,
            min_duration: form.elements["min_duration"].value,
            club: form.elements["club"].value
        };

        if (freeOnlyCheckbox && freeOnlyCheckbox.checked) {
            filters.free_only = "true";
        }

        return filters;
    };

    // Кнопка "Применить фильтры"
    if (applyBtn) {
        applyBtn.addEventListener("click", async () => {
            applyBtn.disabled = true;

            try {
                const filters = collectFilters();
                const slots = await fetchSlots(filters);
                renderSlots(slots);
            } catch (error) {
                console.error(error);
                alert("Не удалось применить фильтры. Попробуйте позже.");
            } finally {
                applyBtn.disabled = false;
            }
        });
    }

    // Кнопка "Сбросить"
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            form.reset();
            // После reset чекбоксы сбросятся к значению по умолчанию (из HTML)

            try {
                const slots = await fetchSlots();
                renderSlots(slots);
            } catch (error) {
                console.error(error);
                alert("Не удалось сбросить фильтры. Попробуйте позже.");
            }
        });
    }
});
