-- Keep a heading and one short introduction with the next table.
-- Figures are not grouped: they float (handbook-typst.typ), so the text after a
-- figure fills the page instead of the figure and its lead-in leaving a gap.
-- A floating figure never lands between the callouts of a run (a pitfall and
-- its decision): pending floats are placed before the run, and a figure of a
-- section that ends in a run floats to the top of a page, not the bottom.
-- Native AST nodes remain intact for Quarto's numbering, links and other writers.
local utf8 = require("utf8")

local function float(block)
  if block.t == "Table" or block.t == "Figure" then return true end
  if block.t == "Para" then
    return #block.content == 1 and block.content[1].t == "Image"
  end
  return block.t == "Div" and (block.identifier:match("^fig%-") ~= nil or block.identifier:match("^tbl%-") ~= nil)
end

local function short(block)
  if block.t ~= "Para" or float(block) then return false end
  local text = pandoc.utils.stringify(block)
  local words = 0
  for _ in text:gmatch("%S+") do words = words + 1 end
  return words > 0 and words <= 80 and (utf8.len(text) or #text) <= 600
end

-- An image float; a Figure or Div that holds a table stays a table float.
local function figure(block)
  if block.t == "Para" then
    return #block.content == 1 and block.content[1].t == "Image"
  end
  if block.t ~= "Figure" and not (block.t == "Div" and block.identifier:match("^fig%-")) then
    return false
  end
  local table = false
  block:walk({ Table = function() table = true end })
  return not table
end

local function callout(block)
  if block.t ~= "Div" then return false end
  for _, class in ipairs(block.classes) do
    if class:match("^callout%-") or class == "callout" then return true end
  end
  return false
end

-- Typst places the floats still pending before a run of callouts starts, so a
-- figure cannot float to the top of a page between two callouts of the run.
local function flush_before_callout_runs(blocks)
  local result = pandoc.List()
  for i, block in ipairs(blocks) do
    local starts_run = callout(block) and blocks[i + 1] ~= nil and callout(blocks[i + 1])
      and not (i > 1 and callout(blocks[i - 1]))
    if starts_run then result:insert(pandoc.RawBlock("typst", "#place.flush()")) end
    result:insert(block)
  end
  return result
end

-- A figure whose section ends in a run of callouts floats to the top of a page:
-- at the bottom of the page it could sit below the first callout of the run
-- while the next callout starts the following page.
local TOP = '#[#show figure.where(kind: "quarto-float-fig"): set figure(placement: top)\n'
  .. '#show figure.where(kind: image): set figure(placement: top)'

local function top_before_callout_runs(blocks)
  local result = pandoc.List()
  for i, block in ipairs(blocks) do
    local before_run = false
    if figure(block) then
      for j = i + 1, #blocks - 1 do
        if blocks[j].t == "Header" then break end
        if callout(blocks[j]) and callout(blocks[j + 1]) then before_run = true; break end
      end
    end
    if before_run then
      result:insert(pandoc.RawBlock("typst", TOP))
      result:insert(block)
      result:insert(pandoc.RawBlock("typst", "]"))
    else result:insert(block) end
  end
  return result
end

function Blocks(blocks)
  if FORMAT ~= "typst" then return nil end
  blocks = top_before_callout_runs(flush_before_callout_runs(blocks))
  local result = pandoc.List()
  for _, block in ipairs(blocks) do
    if float(block) and not figure(block) then
      local lead = pandoc.List()
      if #result > 0 and short(result[#result]) then
        lead:insert(1, result:remove(#result))
      end
      while #result > 0 and result[#result].t == "Header" and result[#result].level > 1 do
        lead:insert(1, result:remove(#result))
      end
      if #lead > 0 then
        -- Flat raw blocks, not a Div: a Div renders as a breakable #block[ and
        -- Typst shrinks an image to that block's remaining space.
        result:insert(pandoc.RawBlock("typst", "#handbook-float-group(lead: ["))
        result:extend(lead)
        result:insert(pandoc.RawBlock("typst", "], body: ["))
        result:insert(block)
        result:insert(pandoc.RawBlock("typst", "])"))
      else result:insert(block) end
    else result:insert(block) end
  end
  return result
end
