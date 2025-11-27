// Здесь логика для AJAX-запросов, обновления статусов,
// применения фильтров без перезагрузки страницы и т.п.

console.log("Moscow Tennis Slots UI loaded");

// Функция, которая запрашивает слоты из API
async function fetchSlots() {
    const response = await fetch("/api/slots", {
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

// Функция, которая перерисовывает tbody таблицы
function renderSlots(slots) {
    const tbody = document.getElementById("slots-table-body");
    if (!tbody) {
        console.warn("Не найден элемент slots-table-body");
        return;
    }

    // Если слотов нет — показываем одну строку с текстом
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

    // Строим HTML для каждой строки
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

// Подписываемся на клик по кнопке "Обновить статусы" после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    const refreshBtn = document.getElementById("refresh-slots-btn");

    if (!refreshBtn) {
        return;
    }

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
});
