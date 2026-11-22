-- Keep a heading and one short introduction with the next table.
-- Figures are not grouped: they float (handbook-typst.typ), so the text after a
-- figure fills the page instead of the figure and its lead-in leaving a gap.
-- A floating figure never lands between the callouts of a run (a pitfall and
-- its decision); see place_around_callout_runs.
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

-- Runs of callouts and the figures around them (Typst only):
-- * before a run, pending floats are placed (#place.flush()) and a marker records
--   where the run starts; before each further callout a marker records the page
--   of that start, so a figure can tell that a run broke across the page;
-- * every figure gets its placement in context (handbook-float-placement in
--   handbook-typst.typ): top when its section ends in a run, bottom on a page
--   where a broken run continues, in the flow when both apply, auto otherwise.
local function in_run(blocks, i)
  return callout(blocks[i]) and (
    (blocks[i + 1] ~= nil and callout(blocks[i + 1])) or (i > 1 and callout(blocks[i - 1])))
end

local function place_around_callout_runs(blocks)
  local result = pandoc.List()
  for i, block in ipairs(blocks) do
    if in_run(blocks, i) then
      if i > 1 and callout(blocks[i - 1]) then
        result:insert(pandoc.RawBlock("typst", "#handbook-run-continue"))
      else
        result:insert(pandoc.RawBlock("typst", "#place.flush()\n#handbook-run-start"))
      end
      result:insert(block)
    elseif figure(block) then
      local before_run = false
      for j = i + 1, #blocks - 1 do
        if blocks[j].t == "Header" then break end
        if callout(blocks[j]) and callout(blocks[j + 1]) then before_run = true; break end
      end
      result:insert(pandoc.RawBlock("typst", "#handbook-placed-figure(before-run: "
        .. tostring(before_run) .. ")["))
      result:insert(block)
      result:insert(pandoc.RawBlock("typst", "]"))
    else result:insert(block) end
  end
  return result
end

function Blocks(blocks)
  if FORMAT ~= "typst" then return nil end
  blocks = place_around_callout_runs(blocks)
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
