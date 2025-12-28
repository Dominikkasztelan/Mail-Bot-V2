from selenium.webdriver.common.by import By

# Importuj logger z odpowiedniego modułu
from src.logger_config import get_logger
logger = get_logger(__name__)

def debug_page_elements(driver):
    """Debuguje elementy strony"""
    logger.info("🔍 Debugowanie elementów strony...")

    # Przyciski
    buttons = driver.find_elements(By.TAG_NAME, "button")
    logger.info(f"Znaleziono {len(buttons)} przycisków na stronie:")
    for i, button in enumerate(buttons):
        try:
            text = button.text
            btn_class = button.get_attribute("class")
            btn_id = button.get_attribute("id")
            aria_label = button.get_attribute("aria-label")
            logger.info(f"Button {i}: Text='{text}', Class='{btn_class}', ID='{btn_id}', aria-label='{aria_label}'")
        except:
            logger.info(f"Button {i}: [Nie udało się odczytać właściwości]")

    # Iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    logger.info(f"Znaleziono {len(iframes)} iframe'ów na stronie:")
    for i, iframe in enumerate(iframes):
        try:
            iframe_id = iframe.get_attribute("id")
            iframe_name = iframe.get_attribute("name")
            iframe_class = iframe.get_attribute("class")
            iframe_src = iframe.get_attribute("src")
            logger.info(
                f"Iframe {i}: ID='{iframe_id}', Name='{iframe_name}', Class='{iframe_class}', Source='{iframe_src}'")
        except:
            logger.info(f"Iframe {i}: [Nie udało się odczytać właściwości]")


def debug_form_elements(driver):
    """Debuguje elementy formularza"""
    logger.info("🔍 Debugowanie elementów formularza...")

    # Pola input
    inputs = driver.find_elements(By.TAG_NAME, "input")
    logger.info(f"Znaleziono {len(inputs)} pól input na stronie:")
    for i, input_field in enumerate(inputs):
        try:
            input_id = input_field.get_attribute("id")
            input_name = input_field.get_attribute("name")
            input_class = input_field.get_attribute("class")
            input_type = input_field.get_attribute("type")
            input_placeholder = input_field.get_attribute("placeholder")
            logger.info(
                f"Input {i}: ID='{input_id}', Name='{input_name}', Class='{input_class}', Type='{input_type}', Placeholder='{input_placeholder}'")
        except:
            logger.info(f"Input {i}: [Nie udało się odczytać właściwości]")

    # Etykiety
    labels = driver.find_elements(By.TAG_NAME, "label")
    logger.info(f"Znaleziono {len(labels)} etykiet na stronie:")
    for i, label in enumerate(labels):
        try:
            label_for = label.get_attribute("for")
            label_text = label.text
            logger.info(f"Label {i}: For='{label_for}', Text='{label_text}'")
        except:
            logger.info(f"Label {i}: [Nie udało się odczytać właściwości]")

    # Selecty
    selects = driver.find_elements(By.TAG_NAME, "select")
    logger.info(f"Znaleziono {len(selects)} pól select na stronie:")
    for i, select in enumerate(selects):
        try:
            select_id = select.get_attribute("id")
            select_name = select.get_attribute("name")
            select_class = select.get_attribute("class")
            logger.info(f"Select {i}: ID='{select_id}', Name='{select_name}', Class='{select_class}'")
        except:
            logger.info(f"Select {i}: [Nie udało się odczytać właściwości]")


def debug_dropdown_structure(driver, dropdown_label):
    """Debuguje strukturę dropdowna po jego otwarciu"""
    logger.info(f"🔍 Debugowanie struktury dropdowna '{dropdown_label}'...")

    debug_script = """
        return (function() {
            // Znajdź wszystkie aktywne/otwarte elementy dropdown
            const activeDropdowns = document.querySelectorAll('[class*="dropdown"][class*="active"], [class*="open"]');

            let result = {
                activeDropdowns: activeDropdowns.length,
                dropdownStructure: []
            };

            // Zbadaj strukturę każdego aktywnego dropdowna
            for (let i = 0; i < activeDropdowns.length; i++) {
                const dropdown = activeDropdowns[i];
                const children = dropdown.children;

                let childInfo = [];
                for (let j = 0; j < children.length; j++) {
                    const child = children[j];
                    childInfo.push({
                        tag: child.tagName,
                        class: child.className,
                        text: child.textContent.trim().substring(0, 20),
                        childCount: child.children.length
                    });
                }

                result.dropdownStructure.push({
                    class: dropdown.className,
                    childCount: children.length,
                    children: childInfo
                });
            }

            return JSON.stringify(result);
        })();
    """

    try:
        dropdown_info = driver.execute_script(debug_script)
        logger.info(f"Informacje o dropdownie '{dropdown_label}': {dropdown_info}")
    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas debugowania dropdowna '{dropdown_label}': {e}")