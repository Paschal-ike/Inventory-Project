# User Roles, Stories & Flows

This describes who uses Hitech Inventory & Cost-Code Control and how, based on the roles and permissions actually implemented in `accounts.models.User.Role` and each app's `permissions.py`.

## Roles

| Role | Scope |
| --- | --- |
| **Administrator** | Bypasses all scoping checks. Full access everywhere. |
| **Store Keeper** | Transacts stock (receive, issue, transfer, adjust) at stores they're assigned to via `StoreAssignment`. |
| **Quarry Manager** | Logs quarry production and transfers stock, scoped to their assigned stockyard(s). |
| **Fleet / Plant Manager** | Manages equipment and work orders. |
| **Procurement Officer** | Manages suppliers, purchase orders, and master data (stores/items/equipment); can receive against any store since procurement is centralized, not site-based. |
| **Cost Accountant / QS** | Manages cost codes; views cost reports. |
| **Project Manager** | Creates and edits projects (if a member), manages project membership, views cost reports. |
| **Viewer** | Read-only, subject to the same store/project scoping as everyone else. |

Two independent scoping layers sit under the org-wide role: **store assignment** (`warehouses.StoreAssignment`) controls which stores a Store Keeper/Quarry Manager can transact in, and **project membership** (`projects.ProjectMembership`) controls which projects a Project Manager can edit or view. Administrators skip both.

## User stories by role

### Administrator
- As an Administrator, I want to create user accounts and assign roles, so the right people have the right level of access.
- As an Administrator, I want to act across every store and project without needing an explicit assignment, so I can resolve issues anywhere.

### Store Keeper
- As a Store Keeper, I want to record a purchase receipt (GRN) against my store, so incoming stock is reflected in the ledger.
- As a Store Keeper, I want to issue items against a cost code (and equipment, if it's a fuel/spare-part issue), so material cost lands on the right project or plant record.
- As a Store Keeper, I want to transfer stock from my store to another, so material can move between depots and sites.
- As a Store Keeper, I want to post a stock count adjustment (increase or decrease) against a cost code, so physical counts stay reconciled with the ledger without editing history.
- As a Store Keeper, I want to see a store's full ledger, so I can trace every movement in or out.

### Quarry Manager
- As a Quarry Manager, I want to log a quarry production receipt into the quarry's stockyard, so material the quarry produces enters the stock ledger at the point of production.
- As a Quarry Manager, I want to transfer produced material out of the stockyard to a depot or site store, so it becomes available to the rest of the operation.

### Fleet / Plant Manager
- As a Fleet Manager, I want to register equipment (asset tag, class, home store, meter type, fuel type), so plant and vehicles are tracked as assets that fuel/spares can be issued against.
- As a Fleet Manager, I want to open a work order against a piece of equipment — breakdown or preventive maintenance — optionally tagged with a cost code, so I can distinguish billable repairs from routine plant overhead.
- As a Fleet Manager, I want to close a work order once the job is done, so its status and closed-at timestamp are accurate.
- As a Store Keeper issuing against a work order, I want the issue tied to that work order's cost code, so parts/fuel cost is attributed correctly without me having to know the accounting rule myself.

### Procurement Officer
- As a Procurement Officer, I want to manage suppliers, so purchasing has an up-to-date, country-scoped vendor list.
- As a Procurement Officer, I want to create a purchase order for a supplier and destination store, so an order for stock exists before goods arrive.
- As a Procurement Officer, I want to receive a purchase order line (fully or partially), so the PO status (Draft → Ordered → Partially Received → Received) reflects reality and the store's stock ledger is updated.
- As a Procurement Officer, I want to receive against any store — not just ones I'm assigned to — because procurement is centralized rather than site-based.
- As a Procurement Officer, I want to create master data (stores, items, equipment), so structural records exist before transactions reference them.

### Cost Accountant / QS
- As a Cost Accountant, I want to create cost codes under a project (or a general plant-overhead code with no project), so every issue and downward adjustment has somewhere valid to post cost to.
- As a Cost Accountant, I want to view cost reports across projects, so I can track material spend against budget.

### Project Manager
- As a Project Manager, I want to create a new project with a short code (used as the cost-code prefix) and currency, so a new job can start tracking cost.
- As a Project Manager, I want to add or remove members on a project I manage, so the right people (store keepers, cost accountants, etc.) can see and work against it.
- As a Project Manager, I want to view the project dashboard and cost reports, so I can track progress and spend.

### Any authenticated user
- As any user, I want to log in, view/edit my profile, and change my password, so I can manage my own account.
- As any user issuing stock, I want to pick from cost codes valid for my project (not just ones I personally manage), so I'm not blocked from doing my job by an accounting-only permission.

## End-to-end flows

### 1. Quarry production → site consumption
1. **Quarry Manager** logs a production receipt into the quarry's stockyard (`stock:quarry_receipt_form`) — stock enters the ledger as `QUARRY_RECEIPT`.
2. **Quarry Manager** (or Store Keeper, if assigned) transfers material from the stockyard to a state depot or project site store (`TRANSFER_OUT` / `TRANSFER_IN` pair).
3. **Store Keeper** at the receiving site store issues material against a project cost code (`ISSUE`) — this is the point material cost lands on a project.

### 2. Procurement → stock on hand
1. **Procurement Officer** creates a supplier and a purchase order (`Draft`) targeting a delivery store.
2. PO is marked `Ordered`.
3. **Procurement Officer** or **Store Keeper** receives PO lines as goods arrive (`stock:receive_form` / `procurement:receive_line`) — stock enters as `PURCHASE_RECEIPT`; PO status moves to `Partially Received` or `Received` depending on quantity received.

### 3. Fleet fuel & spares
1. **Fleet Manager** registers equipment and opens a work order (breakdown or preventive maintenance), optionally tagging it with a cost code.
2. **Store Keeper** issues fuel or spare parts against that equipment/work order — the transaction carries the work order's cost code automatically for billable jobs, or posts to plant overhead if the work order has none.
3. **Fleet Manager** closes the work order once complete.

### 4. Stock count correction
1. A physical count at a store finds a discrepancy.
2. **Store Keeper** posts an `ADJUSTMENT_IN` or `ADJUSTMENT_OUT` against a cost code (required for downward adjustments, since shrinkage/pilferage has to land on something) — never edits a prior posted row, since the ledger is append-only.

### 5. Project cost tracking
1. **Project Manager** creates a project and adds members (store keepers, cost accountant, etc. who need access).
2. **Cost Accountant** creates cost codes under the project.
3. As stock is issued and adjustments are posted against those cost codes, **Cost Accountant** and **Project Manager** view cost reports to track spend against the project.
