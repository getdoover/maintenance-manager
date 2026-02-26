import {defineConfig} from '@rsbuild/core';
import {pluginReact} from '@rsbuild/plugin-react';
import {createModuleFederationConfig, pluginModuleFederation} from '@module-federation/rsbuild-plugin';
import ConcatenatePlugin from './ConcatenatePlugin.ts';

const mfConfig = createModuleFederationConfig({
    name: 'MaintenanceDashboardWidget',
    remotes: {
        // feel free to change these when you're testing & deploying locally.
        // the actual values don't matter (I think?) when this is deployed.
        doover_admin: 'doover_admin@[window.dooverCustomerSite_remoteUrl]',
        customer_site: 'customer_site@[window.dooverAdminSite_remoteUrl]',
    },
    exposes: {
        './MaintenanceDashboardWidget': './src/MaintenanceDashboardWidget',
    },
    shared: {
        react: {singleton: true, requiredVersion: '^18.3.1', eager: true},
        'react-dom': {singleton: true, requiredVersion: '^18.3.1', eager: true},
        'customer_site/hooks': {
            singleton: true,
            requiredVersion: false,
        },
        'customer_site/RemoteAccess': {
            singleton: true,
            requiredVersion: false,
        },
        'customer_site/queryClient': {
            singleton: true,
            requiredVersion: false,
        },
        '@refinedev/core': {
            singleton: true,
            eager: true,
            requiredVersion: false,
        },
        '@tanstack/react-query': {
            singleton: true,
            eager: true,
            requiredVersion: false,
        },

    },
});

export default defineConfig({
    tools: {
        rspack: {
            plugins: [
                new ConcatenatePlugin({
                    source: './dist',
                    destination: './assets',
                    name: 'MaintenanceDashboardWidget.js',
                    ignore: ['main.js'], // Ignore specific files if needed
                }),
            ],
        },
    },
    output: {
        injectStyles: true,
    },

    plugins: [
        pluginReact(),
        pluginModuleFederation(mfConfig),
    ],
    performance: {
        chunkSplit: {
            strategy: 'all-in-one', // Bundle everything into a single file
        },
    },

});