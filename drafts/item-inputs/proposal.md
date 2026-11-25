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

## Who benefits, with examples

The shops and people below are made up. The platform features they use
are real, and are listed at the end of this section.

### One order, three ways

A buyer tells their assistant: "Order the walnut cutting board from this
shop and have it engraved with *The Okafor Family, est. 2019*."

The seller's listing says engraving is required and limited to 25
characters. The buyer's text is 28.

| How the order is placed | What happens |
| --- | --- |
| Through the protocol today | The assistant can add the board to a cart, but there is nowhere to put the engraving. It gives the buyer a link to finish on the shop's website. Some buyers do. Some don't bother. |
| By an agent that operates the website like a person | It types the text into the box. Depending on the site, the last three characters are cut off or the form fails and the agent tries something else. If it goes through, the seller engraves "The Okafor Family, est. 2" on a board that cannot be returned or resold. |
| With this proposal | The listing tells the assistant: one text answer, required, 25 characters at most. Before ordering, the assistant tells the buyer: "That's 28 characters and the limit is 25. Drop the comma and the period?" The buyer agrees. The seller gets text that fits. |

Everything below is that same story from the point of view of each
company involved.

### A jeweller on Shopify

Amara sells name necklaces from a Shopify store. Her product page has a
box: "Name, up to 10 letters." When a buyer types *Zainab*, Shopify saves
it on that line of the cart. Shopify's own developer documentation
describes this feature as being for things "such as gift messages or
engraving text."

Shopify has connected Amara's store to AI assistants. A buyer can now
order her plain chains through an assistant. They cannot order the name
necklace, which is what she mostly sells, because the assistant has no
way to send the name.

What Shopify gets from this proposal:

- Amara's main product becomes something an assistant can sell. Shopify
  earns when she does.
- Shopify builds the connection once. Without a shared format, each
  assistant would need its own way of sending "the name for the
  necklace."
- It closes a gap developers have already asked Shopify about. One
  developer requested that Shopify's own AI cart tool be able to set
  these per-item values, and was told it is not planned.

What it costs Shopify: the *answer* is already stored, but the *rule*
("up to 10 letters") usually lives in the shop's theme or in a
personalization app. Shopify, or those apps, would need to publish the
rules.

### A pet shop on WooCommerce

Dev runs a small WooCommerce store selling dog collars. He uses the
Product Add-Ons extension to add a field to each collar: "Pet's name, up
to 12 characters, add $5."

Here the rule is already written down in a structured way, inside the
extension. One update to that extension could publish every such field
to assistants. Dev would not have to do anything, and neither would the
many other shops using the same extension.

That matters for WooCommerce because its shops are small and numerous.
None of them will write custom code for AI assistants. If it does not
arrive through a plugin update, it does not arrive.

### A football club's store on Salesforce Commerce

A club sells replica shirts. For an extra £15 a fan can add a name of up
to 12 letters and a squad number. The club refuses some names, such as
swear words or a rival player's name.

A large brand like this cares about two things in a sales channel it
does not run itself: the price is the one it set, and its rules are
followed. With this proposal the club publishes the rules and the price,
and checks every name itself. If it rejects one, the assistant is told
so and can ask the fan for another. The club never has to accept an
order it would have refused on its own website.

*(Draft note: how Salesforce Commerce stores a buyer's custom text on an
order line still needs confirming with someone who knows the platform.
Its priced product options are documented.)*

### A marketplace like Etsy

The cutting board at the top of this section is a typical marketplace
order. Four things make marketplaces the companies with the most at
stake.

**A lot of what they sell is personalized.** Wedding signs, name
necklaces, pet portraits, engraved boards. If assistants cannot order
these, a large share of the marketplace cannot be bought through
assistants at all.

**Every seller sets different rules.** Etsy already lets a seller add
questions to a listing, with instructions, a character limit, and a
choice of required or optional. One shop allows 25 characters. The next
asks two questions, a name and a date. A third offers a dropdown of
fonts. This proposal sends those per-listing rules to the assistant as
they are. An approach where each merchant publishes one set of rules for
its whole shop cannot describe a marketplace with millions of sellers.

**A mistake cannot be fixed.** If the board is engraved wrong, the seller
has made something nobody else wants. The buyer opens a case. The seller
refunds or remakes it at their own cost. The marketplace's support team
handles the complaint. Catching the problem before the order is placed
saves all three.

**Three parties need the same record.** The buyer told the assistant,
the assistant told the marketplace, the marketplace told the seller. If
the board arrives wrong, someone has to work out where it went wrong.
With this proposal the order itself records exactly what text was sent.

### "Can't agents already do this by using the website?"

Yes. An agent that clicks through a website can type into an engraving
box. Marketplaces and large shops have three problems with that:

- The agent is guessing the rules from what the page looks like. The
  cutting board example shows what a wrong guess costs.
- The shop cannot tell that agent apart from the bots it already blocks.
- Nothing records that the buyer approved that exact text.

"It already works" also deserves a follow-up question: how often? An
agent that gets the engraving right nine times in ten sounds good until
you are the seller remaking the tenth board. And it works only until the
shop redesigns its product page.

Companies that build assistants able to operate websites also helped
write this protocol. They would not have done that if clicking through
websites were enough.

Companies that joined this protocol did so to get assistants they can
identify, working to rules the company wrote. Today, for personalized
items, they have to send the buyer back to the website or leave the sale
to the kind of agent they were trying to avoid.

### What each company would have to do

- **Shopify, WooCommerce, Salesforce Commerce:** publish the questions
  merchants have already set up, accept the answers with the order, and
  say clearly when an answer is not acceptable. Shop owners change
  nothing on their websites.
- **Etsy and other marketplaces:** the same, listing by listing, using
  the personalization settings sellers already fill in.
- **Nobody** is asked to share anything that is not already shown on the
  product page.

### Where the platform details come from

- Shopify, Cart Lines API (line attributes "such as gift messages or
  engraving text"):
  <https://shopify.dev/docs/api/checkout-ui-extensions/2026-10-rc/target-apis/checkout-apis/cart-lines-api.md>
- Shopify developer community, request for per-item attributes in the
  Storefront MCP server's `update_cart` tool:
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
