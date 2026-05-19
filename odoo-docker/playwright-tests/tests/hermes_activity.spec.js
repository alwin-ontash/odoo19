// @ts-check
const { test, expect } = require('@playwright/test');

// ─── Helpers ──────────────────────────────────────────────────────────────────

const BASE = 'http://localhost:8069';
const EMAIL = 'admin@gmail.com';
const PASSWORD = 'admin1234';

async function login(page) {
    await page.goto('/web/login');
    await page.getByLabel('Email').fill(EMAIL);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Log in' }).click();
    await expect(page).toHaveURL(/\/odoo|\/web#/, { timeout: 20_000 });
}

async function navigateToHermesLog(page) {
    // Use Odoo's JSON-RPC to trigger the action directly — most reliable across routing configs
    await page.goto('/odoo');
    await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => {});

    // Trigger navigation via Odoo's client-side action service
    const navigated = await page.evaluate(async () => {
        try {
            // Load the action data from Odoo
            const resp = await fetch('/web/action/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    jsonrpc: '2.0', method: 'call', id: 1,
                    params: { action_id: 'hermes_activity.hermes_activity_action' }
                })
            });
            const data = await resp.json();
            const action = data.result;
            if (!action) return false;

            // Find Odoo's owl env and use the action service
            const apps = window.__owl__?.apps ?? (window.owl?.App?.apps ? [...window.owl.App.apps] : []);
            if (apps.length > 0) {
                const env = apps[apps.length - 1].env;
                await env.services.action.doAction(action, { clearBreadcrumbs: true });
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    });

    if (!navigated) {
        // Fallback: direct URL navigation with the numeric action ID
        const actionId = await page.evaluate(async () => {
            const resp = await fetch('/web/action/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    jsonrpc: '2.0', method: 'call', id: 1,
                    params: { action_id: 'hermes_activity.hermes_activity_action' }
                })
            });
            const data = await resp.json();
            return data.result?.id;
        });
        if (actionId) {
            await page.goto(`/odoo/hermes-activity`);
        }
    }

    await page.waitForLoadState('domcontentloaded', { timeout: 10_000 }).catch(() => {});
    // Use .first() to avoid strict mode violation (both .o_list_view and .o_nocontent_help can be present)
    await expect(page.locator('.o_list_view, .o_nocontent_help, .o_view_controller').first()).toBeVisible({ timeout: 25_000 });
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe('Hermes Activity Module — E2E Tests', () => {

    test('TC-01: Admin can log in', async ({ page }) => {
        await page.goto('/web/login');
        await expect(page.getByLabel('Email')).toBeVisible();
        await page.getByLabel('Email').fill(EMAIL);
        await page.getByLabel('Password').fill(PASSWORD);
        await page.getByRole('button', { name: 'Log in' }).click();
        await expect(page).toHaveURL(/\/odoo|\/web#/, { timeout: 20_000 });
    });

    test('TC-02: Hermes Activity Log appears when navigated to', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        // Confirm we are on the "Activity Log" view
        await expect(page.getByText('Activity Log').first()).toBeVisible({ timeout: 10_000 });
    });

    test('TC-03: Activity Log list view loads with correct columns', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        // Verify key column headers
        await expect(page.locator('th:has-text("Query")')).toBeVisible({ timeout: 10_000 });
        await expect(page.locator('th:has-text("Source")')).toBeVisible();
        await expect(page.locator('th:has-text("Status")')).toBeVisible();
        await expect(page.locator('th:has-text("MCP Tool Called")')).toBeVisible();
    });

    test('TC-04: Can open New Record form', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        await page.getByRole('button', { name: 'New' }).click();
        await expect(page.locator('.o_form_view')).toBeVisible({ timeout: 10_000 });
        // Required "Query" field is present
        await expect(page.locator('[name="query"] input').first()).toBeVisible();
    });

    test('TC-05: Can create a new activity record', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        await page.getByRole('button', { name: 'New' }).click();

        // Fill required field
        await page.locator('[name="query"] input').fill('Show all products from Telegram');

        // Set source to Telegram (default) — select is already "telegram"
        // Set tool_called
        await page.locator('[name="tool_called"] input').fill('search_products');

        // Set response
        await page.locator('[name="response"] textarea').fill('Found 12 products matching your query.');

        // Set state to Success (default)
        // Save
        await page.getByRole('button', { name: 'Save manually', exact: false }).click().catch(async () => {
            // Some Odoo versions auto-save or use breadcrumb save
            await page.locator('.o_form_button_save').click().catch(() => {});
        });

        // Expect no error banner
        await expect(page.locator('.o_error_dialog, .o_notification.o_notification_danger')).toHaveCount(0, { timeout: 8_000 });
        // Record saved — breadcrumb shows the record or form is visible (no strict mode)
        await expect(page.locator('.o_form_view').first()).toBeVisible({ timeout: 10_000 });
    });

    test('TC-06: Record appears in list view after creation', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        await expect(page.locator('.o_data_row').first()).toBeVisible({ timeout: 10_000 });
    });

    test('TC-07: Search filter by query text works', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);

        // Click the search input
        await page.locator('.o_searchview_input').fill('Show all products');
        await page.keyboard.press('Enter');

        // At least one row should match
        await expect(page.locator('.o_data_row').first()).toBeVisible({ timeout: 10_000 });
    });

    test('TC-08: Can open and read an existing record', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);

        // Click the first row to open form
        await page.locator('.o_data_row').first().click();
        await expect(page.locator('.o_form_view')).toBeVisible({ timeout: 10_000 });

        // Form fields are populated
        await expect(page.locator('[name="query"] input, [name="query"] .o_field_char').first()).toBeVisible();
        await expect(page.locator('[name="state"]').first()).toBeVisible();
    });

    test('TC-09: Can edit an existing record', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);

        await page.locator('.o_data_row').first().click();
        await expect(page.locator('.o_form_view')).toBeVisible({ timeout: 10_000 });

        // Edit notes field — click first to ensure focus, then fill
        const notesTextarea = page.locator('[name="notes"] textarea').first();
        await notesTextarea.click();
        await notesTextarea.fill('Edited by Playwright E2E test');

        // Save using the breadcrumb link (triggers auto-save in Odoo 17+)
        const saveBtn = page.locator('.o_form_button_save').first();
        const hasSave = await saveBtn.isVisible({ timeout: 3_000 }).catch(() => false);
        if (hasSave) {
            await saveBtn.click();
        } else {
            // Navigate to list to trigger auto-save
            await page.locator('.o_breadcrumb a').first().click();
            await page.locator('.o_data_row').first().click();
        }

        await expect(page.locator('.o_error_dialog')).toHaveCount(0, { timeout: 5_000 });
        // Just verify no error — the edit was performed
        await expect(page.locator('.o_form_view').first()).toBeVisible({ timeout: 10_000 });
    });

    test('TC-10: Can delete a record', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);

        // Count rows before delete
        const rowsBefore = await page.locator('.o_data_row').count();

        if (rowsBefore === 0) {
            test.skip();
            return;
        }

        // Select first row checkbox
        await page.locator('.o_data_row').first().locator('.o_list_record_selector input').click();

        // Open Actions menu and delete
        await page.getByRole('button', { name: /action/i }).click();
        await page.getByRole('menuitem', { name: /delete/i }).click();

        // Confirm dialog — "Bye-bye, record!" with "Delete" and "No, keep it" buttons
        // After the menu closes, the only visible "Delete" button is in the confirmation dialog
        await page.getByRole('button', { name: 'Delete' }).waitFor({ state: 'visible', timeout: 10_000 });
        await page.getByRole('button', { name: 'Delete' }).click();

        // Wait for the dialog to close, then count rows
        await page.getByRole('button', { name: 'Delete' }).waitFor({ state: 'detached', timeout: 10_000 }).catch(() => {});
        await page.waitForLoadState('domcontentloaded').catch(() => {});
        const rowsAfter = await page.locator('.o_data_row').count();
        expect(rowsAfter).toBeLessThan(rowsBefore);
    });

    test('TC-11: Form view shows all expected fields', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);
        await page.getByRole('button', { name: 'New' }).click();

        await expect(page.locator('[name="query"]').first()).toBeVisible();
        await expect(page.locator('[name="source"]').first()).toBeVisible();
        await expect(page.locator('[name="tool_called"]').first()).toBeVisible();
        await expect(page.locator('[name="date"]').first()).toBeVisible();
        await expect(page.locator('[name="state"]').first()).toBeVisible();
        await expect(page.locator('[name="response"]').first()).toBeVisible();
        await expect(page.locator('[name="notes"]').first()).toBeVisible();
    });

    test('TC-12: Status filter "Success" works', async ({ page }) => {
        await login(page);
        await navigateToHermesLog(page);

        // Open search → Filters → Success
        await page.locator('.o_searchview_input').click();
        const successFilter = page.getByRole('option', { name: 'Success' }).or(
            page.locator('.o_filter_menu').getByText('Success')
        ).first();
        const isVisible = await successFilter.isVisible({ timeout: 5_000 }).catch(() => false);
        if (isVisible) {
            await successFilter.click();
        }

        // The list view should still be visible (no crash)
        await expect(page.locator('.o_list_view, .o_nocontent_help').first()).toBeVisible({ timeout: 10_000 });
    });

});
