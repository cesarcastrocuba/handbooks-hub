-- Generic table caption and width policy for Quarto pre-ast processing.
-- Run with:
--   filters:
--     - at: pre-ast
--       path: filters/table-layout.lua
--
-- Captioned tables without an identifier receive a deterministic document/content
-- scoped identifier so duplicate captions in different chapter files do not collide.
-- Explicit identifiers and tbl-colwidths attributes are preserved.
-- Width shares are content-derived soft weights; final integer shares are not
-- claimed to satisfy hard min/max bounds.

local utf8 = require("utf8")

-- BEGIN GENERATED INTER BOLD WIDTHS
local INTER_BOLD_WIDTHS = {
  237, 338, 552, 649, 655, 1016, 672, 339, 377, 377, 559, 679,
  334, 468, 334, 388, 674, 431, 630, 646, 676, 622, 649, 582,
  651, 649, 334, 343, 679, 679, 679, 560, 1016, 747, 662, 740,
  722, 607, 587, 750, 747, 281, 584, 719, 565, 932, 762, 771,
  648, 777, 657, 655, 667, 732, 747, 1038, 738, 731, 664, 377,
  388, 377, 487, 476, 365, 581, 630, 588, 630, 596, 398, 632,
  623, 271, 271, 580, 271, 913, 623, 613, 630, 630, 407, 560,
  366, 623, 600, 850, 580, 602, 573, 469, 372, 469, 679,
}
-- END GENERATED INTER BOLD WIDTHS

-- Word table text and geometry. reference.docx Normal is w:sz=21 (10.5 pt); a cell adds 3 pt on
-- each side; 2 pt absorbs rounding. 440 pt is conservative for the A4 text width (470.6 pt) minus
-- the padding and rule of a table inside a callout box.
local WORD_TEXT_PT = 10.5
local CELL_MARGINS_PT = 6
local SAFETY_PT = 2
local USABLE_WIDTH_PT = 440
local FLOOR_MIN_PERCENT = 10
local FLOOR_CAP_WIDE = 20
local FLOOR_CAP_THREE = 28
local FLOOR_CAP_TWO = 35
local FLOOR_MIN_SCALED = 8
local NON_ASCII_EM = 0.62
local CJK_EM = 1.0
local BREAK_CHARS = {[45] = true, [47] = true, [0x2013] = true} -- -, /, en dash

local doc_hash = "document"
local table_index = 0

local function text_length(text)
  return utf8.len(text) or #text
end

local function char_em(code)
  if code >= 32 and code <= 126 then
    return INTER_BOLD_WIDTHS[code - 31] / 1000
  elseif code >= 0x2E80 then
    return CJK_EM
  end
  return NON_ASCII_EM
end

-- The widest piece Word cannot break: whitespace always breaks, and Word also breaks after
-- '-', '/' and an en dash, keeping the break character on the left piece.
local function longest_piece(text)
  local longest, width = 0, 0
  for _, code in utf8.codes(text) do
    if code == 32 or code == 9 or code == 10 or code == 13 then
      if width > longest then longest = width end
      width = 0
    else
      width = width + char_em(code)
      if BREAK_CHARS[code] then
        if width > longest then longest = width end
        width = 0
      end
    end
  end
  if width > longest then longest = width end
  return longest
end

local function hash_text(text)
  local value = 2166136261
  for i = 1, #text do
    value = (value ~ text:byte(i)) * 16777619 & 0xffffffff
  end
  return string.format("%08x", value)
end

local function add_row(row, totals, counts, longest_em, ncols)
  for i = 1, ncols do
    local cell = row.cells[i]
    if cell ~= nil then
      local text = pandoc.utils.stringify(cell)
      totals[i] = totals[i] + text_length(text)
      counts[i] = counts[i] + 1
      local piece = longest_piece(text)
      if piece > longest_em[i] then
        longest_em[i] = piece
      end
    end
  end
end

local function table_widths(tbl)
  local ncols = #tbl.colspecs
  if ncols < 2 or ncols > 100 then
    return nil
  end

  local totals, counts, longest_em = {}, {}, {}
  for i = 1, ncols do
    totals[i] = 0
    counts[i] = 0
    longest_em[i] = 0
  end

  if tbl.head and tbl.head.rows then
    for _, row in ipairs(tbl.head.rows) do
      add_row(row, totals, counts, longest_em, ncols)
    end
  end
  if tbl.bodies then
    for _, body in ipairs(tbl.bodies) do
      if body.head then
        for _, row in ipairs(body.head) do
          add_row(row, totals, counts, longest_em, ncols)
        end
      end
      if body.body then
        for _, row in ipairs(body.body) do
          add_row(row, totals, counts, longest_em, ncols)
        end
      end
    end
  end

  local weights, sum = {}, 0
  for i = 1, ncols do
    local average = counts[i] > 0 and (totals[i] / counts[i]) or 0
    weights[i] = math.max(average, 8)
    sum = sum + weights[i]
  end
  if sum <= 0 then
    return nil
  end

  local percentages, assigned = {}, 0
  for i = 1, ncols do
    percentages[i] = math.max(1, math.floor((weights[i] / sum) * 100))
    assigned = assigned + percentages[i]
  end
  local widest = 1
  for i = 2, ncols do
    if weights[i] > weights[widest] then
      widest = i
    end
  end
  percentages[widest] = percentages[widest] + (100 - assigned)

  -- A column cannot be narrower than its longest unbreakable piece, measured in
  -- Inter Bold em, plus the cell margins. Each column has a floor; the deficit is
  -- taken from all columns that have room above their own floor, largest room
  -- first and repeatedly, so a single narrow donor cannot block the move.
  -- The cap keeps a long word from consuming the page.
  local floors, floor_sum = {}, 0
  for i = 1, ncols do
    local target = math.ceil(
      (longest_em[i] * WORD_TEXT_PT + CELL_MARGINS_PT + SAFETY_PT) / USABLE_WIDTH_PT * 100
    )
    local cap = ncols <= 2 and FLOOR_CAP_TWO or ncols == 3 and FLOOR_CAP_THREE or FLOOR_CAP_WIDE
    target = math.max(FLOOR_MIN_PERCENT, math.min(cap, target))
    floors[i] = target
    floor_sum = floor_sum + target
  end
  if floor_sum > 100 then
    for i = 1, ncols do
      floors[i] = math.max(FLOOR_MIN_SCALED, math.floor(floors[i] * 100 / floor_sum))
    end
  end
  for i = 1, ncols do
    local deficit = floors[i] - percentages[i]
    while deficit > 0 do
      local donor, room = nil, 0
      for j = 1, ncols do
        if j ~= i then
          local available = percentages[j] - floors[j]
          if available > 0 and (donor == nil or available > room
              or (available == room and percentages[j] > percentages[donor])) then
            donor = j
            room = available
          end
        end
      end
      if donor == nil then
        break
      end
      local take = math.min(deficit, room)
      percentages[i] = percentages[i] + take
      percentages[donor] = percentages[donor] - take
      deficit = deficit - take
    end
  end
  return percentages
end

function Pandoc(doc)
  -- The document hash makes auto IDs deterministic and distinct across chapter
  -- files when content differs. Explicit table labels are never replaced.
  local input_file = quarto.doc.input_file
  local project = quarto.project.directory
  if project then
    input_file = pandoc.path.make_relative(input_file, project)
  end
  doc_hash = hash_text(input_file .. "\n" .. pandoc.utils.stringify(doc.blocks))
  table_index = 0
  doc.blocks = doc.blocks:walk({
    Table = function(el)
      local caption = pandoc.utils.stringify(el.caption)
      if caption ~= "" and el.attr.identifier == "" then
        table_index = table_index + 1
        el.attr.identifier = "tbl-auto-" .. doc_hash .. "-" .. table_index
      end
      if el.attr.attributes["tbl-colwidths"] == nil then
        local widths = table_widths(el)
        if widths ~= nil then
          el.attr.attributes["tbl-colwidths"] = "[" .. table.concat(widths, ",") .. "]"
        end
      end
      return el
    end,
  })
  return doc
end
