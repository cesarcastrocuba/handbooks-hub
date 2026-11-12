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
local doc_hash = "document"
local table_index = 0

local function text_length(text)
  return utf8.len(text) or #text
end

local function hash_text(text)
  local value = 2166136261
  for i = 1, #text do
    value = (value ~ text:byte(i)) * 16777619 & 0xffffffff
  end
  return string.format("%08x", value)
end

local function add_row(row, totals, counts, ncols)
  for i = 1, ncols do
    local cell = row.cells[i]
    if cell ~= nil then
      local text = pandoc.utils.stringify(cell)
      totals[i] = totals[i] + text_length(text)
      counts[i] = counts[i] + 1
    end
  end
end

local function table_widths(tbl)
  local ncols = #tbl.colspecs
  if ncols < 2 or ncols > 100 then
    return nil
  end

  local totals, counts = {}, {}
  for i = 1, ncols do
    totals[i] = 0
    counts[i] = 0
  end

  if tbl.head and tbl.head.rows then
    for _, row in ipairs(tbl.head.rows) do
      add_row(row, totals, counts, ncols)
    end
  end
  if tbl.bodies then
    for _, body in ipairs(tbl.bodies) do
      if body.head then
        for _, row in ipairs(body.head) do
          add_row(row, totals, counts, ncols)
        end
      end
      if body.body then
        for _, row in ipairs(body.body) do
          add_row(row, totals, counts, ncols)
        end
      end
    end
  end

  local weights, sum = {}, 0
  for i = 1, ncols do
    local average = counts[i] > 0 and (totals[i] / counts[i]) or 0
    -- Soft content weights: short labels stay compact, prose columns grow.
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

  -- A column narrower than its longest word breaks the word. Keep a small
  -- deterministic floor for narrow tables and take the share from the widest
  -- column that can afford it.
  local floor = ncols <= 3 and 15 or (ncols <= 5 and 11 or 8)
  for i = 1, ncols do
    if percentages[i] < floor then
      local deficit = floor - percentages[i]
      local donor = nil
      for j = 1, ncols do
        if j ~= i and (donor == nil or percentages[j] > percentages[donor]) then
          donor = j
        end
      end
      if donor ~= nil and percentages[donor] - deficit >= floor then
        percentages[i] = floor
        percentages[donor] = percentages[donor] - deficit
      end
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
