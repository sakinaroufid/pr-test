# [Proposal]: Item Inputs — buyer-supplied input on a line item (engraving, monogram, custom text)

> Draft, not yet filed. Intended as an Enhancement Proposal issue on
> `Universal-Commerce-Protocol/ucp`. It picks up the per-item half of the
> direction maintainers set when closing #915 and tracks the use case kept
> open in #349.

## Summary

Add an extension, `dev.ucp.shopping.item_inputs`, that lets a Business
declare the input a product needs from the buyer before it can be made or
shipped (engraving text, a monogram, a name and number on a jersey, a
choice of font), and lets a Platform supply that input on the line item.
The declaration is visible in Catalog, the values travel on Cart and
Checkout line items, the Business validates them, and the Order keeps a
record of what was supplied.

Today a UCP checkout cannot carry this input, so a Business that has
integrated fully must still hand the buyer to its website for every
personalized product.

## Motivation

### The gap

- A shopping `line_item` carries `id`, `item`, `quantity`, `totals` and
  `parent_id`. There is nowhere to put buyer input.
- Product options (`product_option`, `selected_option`) cover choices the
  Business enumerates in advance. Free text cannot be modeled as variants.
- The specification already assumes these products exist: the Return
  Policy extension's example marks "this engraved item" as final sale.
  Nothing lets a Platform say what to engrave.
- Food Checkout (#897) solved the equivalent problem for its vertical with
  `modifications` and a line `note`. Shopping has no counterpart.

### Who is affected

Personalized and made-to-order goods are a large category: engraved
jewelry and watches, monogrammed gifts, custom prints, name-printed
apparel, made-to-measure furniture. For marketplaces built around
handmade and custom goods it is a core part of the catalog. These
products are also disproportionately bought as gifts, which is one of the
most common requests a buyer makes of a shopping agent.

### Prior work

This problem has been approached several times. This proposal builds on
what those threads established.

| Item | Approach | Outcome |
| --- | --- | --- |
| #349 (open) | Request for a buyer note on line items | Kept open "to track the use case" |
| #402, #607 | Free-text `buyer_notes` / `note` on `line_item` | Closed in favor of #481, then #915 |
| #139, #392, #472–#474, #481 | `additional_fields`: Business-defined, checkout-scoped fields with four input types (text, boolean, date, choice) | Closed Jul 27 to "come back with a V2" |
| #915 | `declared_fields`: JSON Schema bags on checkout and line item | Closed Nov 20; maintainers asked for a new EP scoped around standard fields plus profile-declared extensions |
| #455 | Product add-ons as priced choices | Closed for staleness |
| #188 (open) | Ancillaries with text/selection input | No activity |
| #449, #508 | Gift extension; messages explicitly out of scope | Stale |
| Discussion #27 | "Personalized Products on Shopify" | Answered with "use embedded checkout" |

Points raised in review of those threads that this proposal is designed to
answer:

1. **No discovery before a checkout exists.** (wsbrunson on #481) A
   Platform could not learn what would be asked until it had created a
   session, forcing Create → Update → Complete.
2. **Create could not carry values.** (karangoel16, pjordan on #915)
3. **"Required" was undefined.** (karangoel16, pjordan on #915)
4. **Values did not reach the Order.** (pjordan on #915: "engraving text is
   lost after checkout.")
5. **Scope was checkout-level only.** (jingyli, ihoosain on #481 asked
   about line items and cart.)
6. **A second schema distribution system inside `checkout.json`.**
   (gsmith85 on #915) Merchant-specific schemas are also pruned by
   capability intersection unless the Platform lists that merchant's
   capability.
7. **Security and privacy were unaddressed.** (jingyli on #481; pjordan on
   #915: Business-controlled text reaching an agent, and no limit on
   collecting sensitive data.)
8. **Fields must not become a side channel for effectful types.**
   (raginpirate on #481.)

## Why this is in the interest of commerce platforms and marketplaces

### Commerce platforms (Shopify, WooCommerce, Salesforce Commerce)

**They already hold this data. The protocol is the only place it is
missing.** Each platform has a way for a merchant to collect per-item
input on its own storefront:

| Platform | What exists today | How it maps to this proposal |
| --- | --- | --- |
| Shopify | Custom key-value attributes on a cart line, described in Shopify's developer documentation as being for things "such as gift messages or engraving text" | `input_values` on the line item |
| WooCommerce | The Product Add-Ons extension: short text, long text, date picker and other field types, with character limits and input restrictions | `inputs` declarations with `text` and `date` types and `max_length` |
| Salesforce B2C Commerce | Product options for priced extras bought with a product *(free-text personalization on line items to be confirmed with Salesforce)* | `choice` inputs with a `price` |

So for a commerce platform this is a mapping exercise onto fields its
merchants have already configured, not a new feature to build.

**Their merchants' personalized products are shut out of the agent
channel.** A merchant on any of these platforms who sells engraved or
made-to-order goods gets no benefit from the platform's protocol
integration for those products: the checkout hands off to the website.
Commerce platforms earn on the volume their merchants sell, so products
that cannot be sold through the channel are revenue the platform has
invested in and cannot collect.

**Without a standard, each platform carries the gap separately.** A
community feature request reports that Shopify's own storefront MCP
server cannot set line attributes when updating a cart, and that
supporting it is not on the roadmap. The same hole exists in the protocol
layer. If each agent platform fills it differently, every commerce
platform maintains one mapping per agent platform. A single declared
shape means one mapping.

**Unstructured key-value data is the wrong thing to hand an agent.** A
bare attribute such as `engraving: "..."` tells an agent nothing about
length limits, whether it is required, or what it costs. The agent
guesses, and the merchant finds out at fulfillment. Declared inputs move
the validation to before the order exists.

**It gives their app ecosystems a target.** Personalization on Shopify
and WooCommerce is largely delivered by third-party apps and add-ons.
Today none of that configuration is visible to an agent (see Discussion
#27, where a Shopify seller asked exactly this). A standard declaration
gives those apps one format to publish to. For WooCommerce in
particular, a single plugin could expose existing Product Add-Ons fields
to every agent with no work by the merchant.

**For enterprise brands, it preserves control.** Brands on Salesforce
Commerce that offer personalization as a premium service (monogrammed
leather goods, engraved jewelry, name-printed team apparel) care that the
rules and the price are the brand's own. Declared inputs keep the brand
as the author of those rules in a channel it does not otherwise control.

### Marketplaces (Etsy and others built on custom and handmade goods)

**Personalized listings are core inventory, not an edge case.** For a
marketplace of handmade and custom goods, a protocol that cannot carry
personalization excludes a large part of the catalog from agent checkout.

**Rules are set per listing by each seller, which is the case this
design is built for.** Etsy lets a seller add personalization questions
to a listing, with instructions, a character limit on text answers, a
required-or-optional setting, and several question types including text
and dropdown. That is the same information as an `inputs` declaration.
With millions of sellers each setting their own rules, only a
per-product declaration works: a single merchant-level schema, as in
#915, cannot describe them.

**Mistakes cannot be undone.** A custom item made with the wrong text is
usually not returnable and cannot be resold. On a marketplace the cost
lands as a buyer case, a refund or remake by the seller, and a support
contact for the marketplace. Catching an invalid or missing value before
the order is placed is worth more here than for any other product type.

**The seller, not the marketplace, makes the item.** The buyer's input
has to pass accurately from the agent, through the marketplace, to a
third-party seller. A structured value recorded on the order gives all
three parties the same record when something is disputed.

**Gifts.** Personalized goods are disproportionately bought as gifts,
and gift shopping is among the most common tasks buyers hand to an
agent. A marketplace strong in gifts has the most to gain from agents
being able to complete these purchases.

**The alternative is agents the marketplace does not control.**
Browser-driving agents can already type into a personalization box.
They infer the rules from the page, carry no agent identity or record of
buyer consent, and are hard to tell apart from the automated traffic
marketplaces block. A marketplace that has chosen protocol integration
for those reasons currently has to leave its personalized listings to
exactly that kind of agent, or out of agent checkout altogether.

### What it asks of them

- **Commerce platforms:** publish the fields merchants have already
  configured as `inputs` in catalog responses, accept `input_values` on
  line items, and return validation errors. No change to merchant
  storefronts.
- **Marketplaces:** the same, per listing, using the personalization
  settings sellers already maintain.
- **Neither** is asked to share data it does not already show on a
  product page.

### References for this section

- Shopify, Cart Lines API (line attributes "such as gift messages or
  engraving text"):
  <https://shopify.dev/docs/api/checkout-ui-extensions/2026-10-rc/target-apis/checkout-apis/cart-lines-api.md>
- Shopify developer community, feature request for line item attributes
  in the Storefront MCP server `update_cart` tool:
  <https://community.shopify.dev/t/feature-request-storefront-mcp-server-update-cart-tool-should-support-line-item-attributes/28128>
- WooCommerce, Product Add-Ons:
  <https://woocommerce.com/products/product-add-ons/>
- Salesforce Trailhead, B2C product options:
  <https://trailhead.salesforce.com/content/learn/modules/b2c-catalog-category-product/b2c-product-sets-bundles-options>
- Etsy Help, How to Offer Personalized Listings:
  <https://help.etsy.com/hc/en-us/articles/360000344528-How-to-Offer-Personalized-Listings>
- Etsy developer documentation, personalization question types:
  <https://developer.etsy.com/documentation/tutorials/personalization/multiple-and-new-question-type-support>

## Goals

- A Platform can tell from Catalog that a product needs buyer input, what
  the rules are, and whether it costs extra, before creating a cart or
  checkout.
- A Platform can supply the input on Create or Update, per line item.
- The Business validates the input and returns errors a Platform can act
  on without guessing.
- The Order records what the buyer supplied.
- A Platform that does not support the extension, or an input type, can
  still complete the purchase through the existing handoff.
- No merchant-specific schema is needed for the common cases.

## Non-Goals

- **Checkout-level fields** such as gift message, order note and delivery
  instructions. Those belong to the successor of #481/#915. This proposal
  is intended to share its input-type vocabulary with that work.
- **File or image uploads, and proof approval.** Photo products and
  anything needing a visual preview continue to use `continue_url` in
  this version.
- **Merchant-defined schemas.** Covered by the profile-declared extension
  direction from #915.
- **Add-on products** such as warranties or gift wrap sold as a separate
  priced line. Those are items, not input.
- **Gift recipients** (#449/#508) and **food modifications** (#897).
- **Changing how payment handlers, capabilities or fulfillment options are
  negotiated.**

## Detailed Design

### Capability

`dev.ucp.shopping.item_inputs` extends `dev.ucp.shopping.catalog.search`,
`dev.ucp.shopping.catalog.lookup`, `dev.ucp.shopping.cart`,
`dev.ucp.shopping.checkout` and `dev.ucp.shopping.order`, following the
composition pattern of `dev.ucp.shopping.purchase_options`.

Both parties advertise the input types they support in `config`. The
active set is the intersection, as proposed in #481:

```json
{
  "dev.ucp.shopping.item_inputs": [
    {
      "version": "2026-xx-xx",
      "config": { "supported_types": ["text", "choice", "boolean", "date"] }
    }
  ]
}
```

Because the extension is in the `dev.ucp` namespace and inputs are
described as data rather than as merchant schemas, capability
intersection does not prune a specific merchant's fields (review point 6).

### Declaration in Catalog

A catalog variant gains a response-only `inputs` array. It is declared on
the variant because rules can differ by variant (a 38 mm case holds fewer
characters than a 42 mm one). A Business with identical rules across
variants repeats the declaration.

```json
{
  "id": "var_watch_42_steel",
  "title": "Classic Watch, 42 mm, Steel",
  "price": { "amount": 24900, "currency": "USD" },
  "inputs": [
    {
      "id": "engraving_text",
      "label": "Case back engraving",
      "description": "Engraved on the case back. Letters, numbers and basic punctuation.",
      "required": false,
      "input": { "type": "text", "min_length": 1, "max_length": 20 },
      "price": { "amount": 1500, "currency": "USD" }
    },
    {
      "id": "engraving_font",
      "label": "Engraving font",
      "required": false,
      "depends_on": "engraving_text",
      "input": {
        "type": "choice",
        "options": [
          { "value": "serif", "label": "Serif" },
          { "value": "script", "label": "Script" }
        ]
      }
    }
  ]
}
```

Fields of an input declaration:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Stable within the variant. Used to submit a value. |
| `label` | string | Short display name. |
| `description` | string | Optional guidance for the buyer. |
| `required` | boolean | If `true`, the line cannot be purchased without a value. |
| `input` | object | Type and constraints. See below. |
| `price` | amount | Optional. Indicative extra charge per unit when a value is supplied. The line's totals are authoritative. |
| `depends_on` | string | Optional. `id` of another input; this one applies only when that one has a value. |

Input types reuse the vocabulary reviewed in #481:

| `type` | Constraints | Value |
| --- | --- | --- |
| `text` | `min_length`, `max_length`, `multiline` | string |
| `choice` | `options[]` of `{value, label, price?}` | an option `value` |
| `boolean` | none | `true` or `false` |
| `date` | `min`, `max` (YYYY-MM-DD) | YYYY-MM-DD string |

`required` has one meaning: a Business **MUST NOT** report a checkout as
`ready_for_complete` while a required input on any line has no valid
value (review point 3).

### Values on Cart and Checkout

A line item gains two fields:

- `inputs` (response only): the declarations that apply to this line, as
  the Business evaluates them for this cart or checkout.
- `input_values` (request and response): what the buyer supplied.

```json
{
  "line_items": [
    {
      "item": { "id": "var_watch_42_steel" },
      "quantity": 1,
      "input_values": [
        { "id": "engraving_text", "value": "Happy 60th, Dad" },
        { "id": "engraving_font", "value": "script" }
      ]
    }
  ]
}
```

Rules:

- `input_values` is accepted on Create and on Update (review points 1 and
  2). Like `line_items`, an Update replaces the previous set for that
  line.
- One set of values applies to every unit on the line. Units that need
  different input are separate lines; a Business that supports this
  extension **MUST** accept the same variant on more than one line.
- A Platform **MUST** send only values the buyer supplied or confirmed. It
  **MUST NOT** invent a value to satisfy a required input.
- The Business echoes accepted values. It **MUST NOT** silently alter a
  value; if it normalizes one (for example trimming whitespace) it returns
  the stored form and a `warning` message.
- Cart carries the same two fields so a cart can be built and estimated
  before checkout (review point 5).

### Validation

Problems are reported in `messages[]` with a `path` to the value, using
the existing error structure:

```json
{
  "type": "error",
  "code": "item_input_invalid",
  "path": "$.line_items[0].input_values[0]",
  "content": "Engraving is limited to 20 characters; 23 were supplied.",
  "severity": "recoverable"
}
```

| Code | Meaning |
| --- | --- |
| `item_input_required` | A required input has no value. |
| `item_input_invalid` | The value breaks a declared constraint. |
| `item_input_rejected` | The value is well-formed but refused by Business policy (for example prohibited wording). |
| `item_input_unknown` | The `id` is not declared for this line. |

All four are `recoverable`: the Platform can fix them with the buyer and
resubmit. A Business that cannot accept an input through the protocol at
all (unsupported type, needs a visual proof) uses a `requires_buyer_input`
severity and `continue_url`, which is the existing handoff.

### Effects on price, delivery and returns

Each effect uses a mechanism the protocol already has:

- **Price.** The Business recalculates the line and checkout `totals`.
  The declared `price` is advance notice so the Platform can tell the
  buyer before submitting.
- **Delivery time.** Reflected in the Fulfillment extension's options and
  expectations.
- **Returns.** Reflected in `policies[]` targeting the line, as in the
  Return Policy extension's engraved-item example.

Inputs **MUST NOT** change which payment handlers are offered, or any
negotiated capability (review point 8).

### Order

An order line item gains a read-only `inputs` array recording what was
supplied, as it stood at checkout (review point 4):

```json
{
  "inputs": [
    {
      "id": "engraving_text",
      "label": "Case back engraving",
      "type": "text",
      "value": "Happy 60th, Dad"
    },
    {
      "id": "engraving_font",
      "label": "Engraving font",
      "type": "choice",
      "value": "script",
      "value_label": "Script"
    }
  ]
}
```

It is a historical record. The `id` need not still resolve in the catalog.

### Fallback when the extension is not active

If the Platform does not support the extension, or a required input has a
type outside the active set, the Business returns the checkout as
`requires_escalation` with a `continue_url`, exactly as it would today.
No purchase that works now stops working.

### Security and privacy

Review point 7.

- `label`, `description` and option labels are Business-controlled text
  that may reach a language model. A Platform **MUST** treat them as
  untrusted display content, not as instructions.
- Values are buyer-supplied text that reaches Business systems. A
  Business **MUST** treat them as untrusted input.
- A Business **MUST NOT** use item inputs to collect payment credentials,
  authentication secrets, government identifiers or other sensitive
  personal data. Inputs describe how a product is to be made.
- A Platform **SHOULD** decline to submit a value that plainly falls in
  those categories and tell the buyer why.
- Values may contain personal data (a name, a date). Existing retention
  guidance for order data applies.

## Alternatives Considered

- **A free-text note on the line (#402, #607).** Simple, but the Platform
  cannot learn the rules in advance, the Business cannot return a precise
  error, and required input cannot be expressed. A note is still useful
  for unstructured requests and could be a separate small addition; Food
  Checkout already has one.
- **Checkout-scoped additional fields (#481).** Right shape for
  order-level questions. It does not attach to a line and is discoverable
  only after a checkout exists.
- **JSON Schema bags on the checkout (#915) or merchant schemas in the
  business profile.** Flexible, and right for merchant-specific data. For
  this use case one schema per merchant cannot express rules that differ
  per product, it needs a schema renderer on every Platform, and it is
  subject to capability pruning.
- **Variants.** Works for enumerable choices and is what the protocol
  does today. Free text cannot be enumerated.
- **Embedded checkout or `continue_url`.** Works today and remains the
  fallback. It is the handoff this proposal aims to make unnecessary for
  the common cases.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Overlap with the successor to #481/#915 | Scope is per-item only; input types are shared with that work so both can use one vocabulary |
| Too simple for real merchants (previews, uploads, dependent rules) | Version 1 covers text, choice, boolean and date; anything else falls back to handoff; `input.type` is open for later types |
| Prompt injection through labels, abuse through values | Normative handling rules above |
| Used to collect sensitive data | Explicit prohibition; Platforms may refuse |
| Platforms inventing values to get past a required field | Explicit prohibition; values must come from the buyer |
| Breaking existing implementations | Additive and negotiated; absent the extension, behavior is unchanged |

## Open Questions for the Tech Council

1. Should `price` on an input be allowed in version 1? #481 proposed that
   fields must not affect totals. Personalization commonly carries a
   charge, and totals are already Business-authoritative on every update.
2. Variant-level or product-level declaration, or both?
3. Should this share a schema file for input types with the checkout-level
   fields work, or should one EP cover both scopes?
4. Is `depends_on` worth including, or should dependent rules be left to
   validation errors in version 1?
5. Should a plain line `note`, as in Food Checkout, be added to Shopping
   alongside this for unstructured requests?

## Test Plan

- Schema lint and example validation for every new example.
- Conformance cases for: declaration present in catalog; value accepted
  on Create; value accepted on Update; missing required value blocks
  `ready_for_complete`; each error code; totals change when a priced
  input is supplied; order records the values; unsupported type falls
  back to `requires_escalation`.
- Cases across REST, MCP and A2A bindings.
- A reference implementation in the samples repository: a store selling
  an engravable product, and a client that reads the declaration,
  collects the text and completes the purchase.

## Graduation Criteria

- **Provisional:** Tech Council agrees the scope and its relationship to
  the checkout-level fields work.
- **Candidate:** schemas, specification text and conformance tests merged;
  at least one Business and one Platform implementation interoperating.
- **Stable:** two independent Business implementations and two independent
  Platform implementations, including at least one marketplace with
  per-product rules.

## Implementation History

- Draft prepared; not yet submitted.
