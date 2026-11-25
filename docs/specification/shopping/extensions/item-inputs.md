<!--
   Copyright 2026 UCP Authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
-->

# Item Inputs Extension

## Overview

Some products cannot be made until the buyer says something about them: the
text to engrave on a watch, the initials on a towel, the name on a shirt. The
Item Inputs extension lets a Business say what it needs to know, lets a
Platform send the buyer's answers with the line, and keeps those answers on the
resulting Order.

Today a line item is a variant and a quantity. A Business that sells an
engravable watch has no way to ask for the engraving in its catalog, a Platform
has no way to send it, and a checkout for that watch has to be handed off to
the Business's website.

An **item input** is one question the Business asks about an item: an `id`, a
`label`, whether an answer is `required`, and the kind of answer it accepts.
The Business declares inputs on the variant. The Platform answers them on the
line by `id`. The Business checks every answer and is the only party that
decides whether it is acceptable.

This extension adds:

- `inputs[]` on a catalog variant and on a cart or checkout line — the
    questions the Business asks. Response-only.
- `input_values[]` on a cart or checkout line — the buyer's answers. A
    Platform writes them; the Business echoes the ones it holds.
- `input_values[]` on an Order line — the record of what the buyer supplied,
    as it stood at checkout.
- Four error codes and one warning code for reporting problems with an answer.

**Dependencies:**

- One or more of the parent capabilities this extension extends: Catalog
  Search, Catalog Lookup, Cart, Checkout, or Order.

An input describes how one line is to be made. It never adds, removes, or
changes other lines, and it never changes which payment handlers or
capabilities are in effect. Questions about the order as a whole, such as
delivery instructions, are not item inputs.

## Discovery

Businesses advertise item inputs in their profile:

<!-- ucp:example schema=profile def=business_schema extract=$.ucp.capabilities target=$.ucp.capabilities -->
```json
{
  "ucp": {
    "version": "{{ ucp_version }}",
    "capabilities": {
      "dev.ucp.shopping.item_inputs": [
        {
          "version": "{{ ucp_version }}",
          "extends": [
            "dev.ucp.shopping.catalog.search",
            "dev.ucp.shopping.catalog.lookup",
            "dev.ucp.shopping.cart",
            "dev.ucp.shopping.checkout",
            "dev.ucp.shopping.order"
          ],
          "spec": "https://ucp.dev/{{ ucp_version }}/specification/shopping/extensions/item-inputs",
          "schema": "https://ucp.dev/{{ ucp_version }}/schemas/shopping/item_inputs.json"
        }
      ]
    }
  }
}
```

Advertising this extension means the Business returns `inputs` for variants
that have them, accepts and validates `input_values` on cart and checkout
lines, and preserves accepted answers on the resulting Order line.

A Platform that advertises this extension **MUST** be able to collect an
answer for each of the four well-known input types.

## Schema

### Item Input

{{ schema_fields('types/item_input', 'shopping/extensions/item-inputs') }}

### Item Input Value

{{ schema_fields('types/item_input_value', 'shopping/extensions/item-inputs') }}

### Variant Inputs

{{ extension_schema_fields('item_inputs.json#/$defs/variant_inputs', 'shopping/extensions/item-inputs') }}

### Line Item with Item Inputs

{{ extension_schema_fields('item_inputs.json#/$defs/line_item', 'shopping/extensions/item-inputs') }}

### Order Item Input Value

{{ schema_fields('types/order_item_input_value', 'shopping/extensions/item-inputs') }}

## Declaring inputs

### Where inputs are declared

Inputs are declared on the variant, because the rules can differ between
variants of one product: a 38 mm watch case holds fewer characters than a
42 mm one. A Business whose rules are the same for every variant repeats the
declaration on each.

Where `inputs` is absent, the variant needs nothing from the buyer and nothing
about it changes.

The `id` of an input is unique among the inputs of its variant. It need not be
unique across variants or products.

### Input types

`input.type` says what kind of answer is expected. Four values are well known:

| `type` | Limits the Business can state | The answer |
| :--- | :--- | :--- |
| `text` | `min_length`, `max_length`, `multiline` | A string |
| `choice` | `options[]`, each with a `value` and a `label` | One option's `value` |
| `boolean` | None | `true` or `false` |
| `date` | `min`, `max` | A `YYYY-MM-DD` string |

`type` is an open identifier. A Platform **MUST NOT** treat a type it does not
recognize as one of the well-known types. If such an input is `required`, the
Platform cannot complete the line itself and follows
[Fallback](#fallback).

The limits a Business states are the ones a Platform can check before sending
an answer. A Business **MAY** apply further rules it does not state, such as
refusing offensive text, and reports a breach of them as an error (see
[Validation](#validation)).

### Required and optional

`required` has one meaning. Where an input is `required`, the Business
**MUST NOT** report a checkout as `ready_for_complete` while that input has no
valid answer on any line that declares it.

An optional input with no answer means the buyer did not ask for it: the watch
is sold without engraving.

### Price

An input **MAY** carry a `price`: the extra charge per unit when an answer is
supplied. A choice option **MAY** carry its own `price`, charged in addition.

These amounts let a Platform tell the buyer the cost before sending an answer.
They are indicative. Once an answer is on a line, the line's `item.price` and
`totals` state what the buyer pays, and a Platform **MUST** re-render from the
response.

## Supplying answers

A Platform answers inputs by sending `input_values` on the line:

<!-- ucp:example schema=shopping/item_inputs def=dev.ucp.shopping.checkout op=create direction=request -->
```json
{
  "line_items": [
    {
      "item": { "id": "gid://example/Variant/watch-42-steel" },
      "quantity": 1,
      "input_values": [
        { "id": "engraving_text", "value": "Happy 60th, Dad" },
        { "id": "engraving_font", "value": "script" }
      ]
    }
  ]
}
```

Rules for a Platform:

- It **MUST** send only answers the buyer supplied or confirmed. It
    **MUST NOT** make up an answer to satisfy a `required` input.
- It **MUST** send the complete set of answers for a line each time it writes
    the line. An input with no entry is unanswered.
- It **MUST NOT** send more than one entry for the same `id` on a line.
- It **SHOULD** check an answer against the limits the Business stated before
    sending it, and tell the buyer about a breach instead of sending it.

Rules for a Business:

- It **MUST** validate every answer against the line's `inputs`, whatever
    checks the Platform made.
- It **MUST** echo the answers it holds in `input_values` on the response.
- It **MUST NOT** silently change an answer. If it stores a different form
    than it received, such as text with surrounding spaces removed, it returns
    the stored form and reports the change with an `item_input_changed`
    warning.
- It **MUST** accept answers on Create as well as on Update, so that a
    Platform that read the inputs from the catalog needs no extra round trip.

### One set of answers per line

The answers on a line apply to every unit on it. Two watches with the same
engraving are one line with `quantity: 2`. Two watches with different
engravings are two lines.

A Business that advertises this extension **MUST** accept the same variant on
more than one line of a cart or checkout, and **MUST NOT** merge lines whose
answers differ.

### The line's inputs are authoritative

A cart or checkout line carries its own `inputs`: the questions as the
Business evaluates them for this line now. They can differ from what the
catalog showed, because the catalog was read earlier or because the Business
applies rules that depend on the cart.

A Platform **MUST** treat the line's `inputs` as the current rules and
**MUST NOT** assume the catalog's still apply.

## Validation

A Business reports a problem with an answer in `messages[]`, with a `path` to
the entry in `input_values` or, where an answer is missing, to the entry in
`inputs`.

| Code | Meaning | What a Platform does |
| :--- | :--- | :--- |
| `item_input_required` | A required input has no answer | Ask the buyer for it |
| `item_input_invalid` | The answer breaks a stated limit | Tell the buyer the limit and ask again |
| `item_input_rejected` | The answer is well formed but the Business refuses it | Tell the buyer and ask for a different answer |
| `item_input_unknown` | The `id` is not one of the line's inputs | Drop the entry; re-read the line's `inputs` |

All four are `recoverable`: the Platform can put them right with the buyer and
send the line again.

An answer that is too long:

<!-- ucp:example schema=shopping/checkout target=$.messages -->
```json
[
  {
    "type": "error",
    "code": "item_input_invalid",
    "path": "$.line_items[0].input_values[0]",
    "content": "Engraving is limited to 20 characters; 23 were supplied.",
    "severity": "recoverable"
  }
]
```

A required answer that is missing:

<!-- ucp:example schema=shopping/checkout target=$.messages -->
```json
[
  {
    "type": "error",
    "code": "item_input_required",
    "path": "$.line_items[0].inputs[0]",
    "content": "Tell us the name to print on the shirt.",
    "severity": "recoverable"
  }
]
```

A Business **SHOULD NOT** say why it rejected an answer in more detail than the
buyer needs. "This text cannot be engraved" is enough.

While any of these errors stands, the checkout stays `incomplete`.

## Effects on the rest of the checkout

Answering an input is a cart or checkout mutation, and the Business response is
authoritative for everything derived from it. Each effect is reported through
the mechanism that already owns it:

- **Price.** The line's `item.price` and `totals`, and the checkout `totals`.
- **Delivery.** Fulfillment options and expectations, where a made-to-order
    item takes longer. See the
    [Fulfillment Extension](fulfillment.md).
- **Returns.** `policies[]` targeting the line, where a personalized item
    cannot be returned. See the
    [Return Policy Extension](return-policy.md).

An answer **MUST NOT** change which payment handlers are offered or which
capabilities are active.

## Fallback

Three situations leave a Platform unable to answer an input itself:

- The Platform does not advertise this extension.
- A `required` input has a type the Platform does not recognize.
- The Business needs something this extension cannot carry, such as an
    uploaded photo or the buyer's approval of a proof.

In each, the Business reports the checkout as `requires_escalation` with a
`continue_url`, exactly as it does for any other information it cannot collect
through the API. No purchase that works without this extension stops working
with it.

A Business **MUST NOT** treat a line as answered because the Platform did not
advertise the extension. A watch whose engraving is optional is sold without
engraving; a shirt whose name is required is handed off.

## Security and privacy

- `label`, `description`, and option labels are text the Business writes that
    can reach a language model. A Platform **MUST** treat them as content to
    show the buyer, never as instructions.
- Answers are text the buyer writes that reaches the Business's systems. A
    Business **MUST** treat them as untrusted input.
- A Business **MUST NOT** use item inputs to collect payment credentials,
    passwords, government identifiers, or other sensitive personal data. An
    input asks how an item is to be made.
- A Platform **SHOULD** decline to send an answer that plainly belongs to one
    of those categories, and tell the buyer why.
- Answers can contain personal data, such as a name or a date of birth on a
    gift. They are part of the Order and are handled as the rest of it is.

## Examples

### Catalog: a watch that can be engraved

The steel watch can be engraved for $15. Engraving is optional. If the buyer
wants it, they can also choose a font.

<!-- ucp:example schema=shopping/item_inputs def=get_product_response op=get_product target=$.product.variants[0] -->
```json
{
  "id": "gid://example/Variant/watch-42-steel",
  "title": "42 mm, Steel",
  "description": { "plain": "Automatic movement, sapphire crystal." },
  "price": { "amount": 24900, "currency": "USD" },
  "inputs": [
    {
      "id": "engraving_text",
      "label": "Case back engraving",
      "description": { "plain": "Up to 20 characters. Letters, numbers and basic punctuation." },
      "required": false,
      "input": { "type": "text", "max_length": 20 },
      "price": { "amount": 1500, "currency": "USD" }
    },
    {
      "id": "engraving_font",
      "label": "Engraving font",
      "required": false,
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

### Checkout: the engraving is accepted

The Platform sent the engraving and the font. The Business accepted both. The
line's price is now $264: the watch plus the engraving.

<!-- ucp:example schema=shopping/item_inputs def=dev.ucp.shopping.checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "chk_abc123",
  "status": "ready_for_complete",
  "currency": "USD",
  "line_items": [
    {
      "id": "li_1",
      "item": { "id": "gid://example/Variant/watch-42-steel", "title": "Classic Watch, 42 mm, Steel", "price": 26400 },
      "quantity": 1,
      "totals": [
        { "type": "subtotal", "amount": 26400 },
        { "type": "total", "amount": 26400 }
      ],
      "inputs": [
        {
          "id": "engraving_text",
          "label": "Case back engraving",
          "description": { "plain": "Up to 20 characters. Letters, numbers and basic punctuation." },
          "required": false,
          "input": { "type": "text", "max_length": 20 },
          "price": { "amount": 1500, "currency": "USD" }
        },
        {
          "id": "engraving_font",
          "label": "Engraving font",
          "required": false,
          "input": {
            "type": "choice",
            "options": [
              { "value": "serif", "label": "Serif" },
              { "value": "script", "label": "Script" }
            ]
          }
        }
      ],
      "input_values": [
        { "id": "engraving_text", "value": "Happy 60th, Dad" },
        { "id": "engraving_font", "value": "script" }
      ]
    }
  ],
  "totals": [
    { "type": "subtotal", "amount": 26400 },
    { "type": "tax", "amount": 2112 },
    { "type": "total", "amount": 28512 }
  ],
  "links": [ ... ]
}
```

### Checkout: the Business stored a different form

The buyer's text had a trailing space. The Business removed it and says so.

<!-- ucp:example schema=shopping/checkout target=$.messages -->
```json
[
  {
    "type": "warning",
    "code": "item_input_changed",
    "path": "$.line_items[0].input_values[0]",
    "content": "Spaces at the end of the engraving were removed."
  }
]
```

### Order: what was supplied

The Order line records the answers as the Business accepted them. The record
does not change if the Business later changes the watch's inputs.

<!-- ucp:example schema=shopping/item_inputs def=dev.ucp.shopping.order op=read -->
```json
{
  "ucp": { ... },
  "id": "ord_8f3e2a",
  "checkout_id": "chk_abc123",
  "permalink_url": "https://example.com/orders/8f3e2a",
  "currency": "USD",
  "line_items": [
    {
      "id": "li_1",
      "item": { "id": "gid://example/Variant/watch-42-steel", "title": "Classic Watch, 42 mm, Steel", "price": 26400 },
      "quantity": { "original": 1, "total": 1, "fulfilled": 0 },
      "totals": [ ... ],
      "status": "processing",
      "input_values": [
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
  ],
  "totals": [ ... ],
  "fulfillment": { ... }
}
```
