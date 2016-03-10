local plugin = ...

function plugin.setup()
    plugin.events.add_callback("MessageReceived", plugin, plugin.on_message, 0)
    plugin.commands.register_command("luatest", plugin.luatest_command, plugin, nil, nil, true)
end

function plugin.on_message(event)
    plugin.logger.info("Got message: " .. event.message)
end

function plugin.luatest_command(protocol, caller, source, command, raw_args, args)
    plugin.logger.info("Running lua command")

    if #raw_args == 0 then
        caller.respond("Usage: {CHARS}"..command.." <message>")
        return
    end

    source.respond("[LuaTest] " .. string.reverse(raw_args))
end

return plugin
